"""Original, reviewed diagnostic items and deterministic recovery content.

The benchmark samples each SAT content domain, not every subskill. Results are
provisional evidence, never an official scaled-score estimate.
"""
import learning
import random
import re

JAMES_LU = {'name': 'James Lu SAT Prep', 'url': 'https://www.skool.com/sat/about',
            'note': 'Desmos and grammar emphasis informed by James Lu’s public SAT prep. Original Mentics example; not affiliated.'}


def domain(skill):
    if skill in {'central_ideas', 'command_of_evidence_text', 'command_of_evidence_quant', 'inferences'}:
        return 'Information and Ideas'
    if skill in {'words_in_context', 'text_structure_purpose', 'cross_text_connections'}:
        return 'Craft and Structure'
    if skill in {'transitions', 'rhetorical_synthesis', 'act_english_rhetoric'}:
        return 'Expression of Ideas'
    resolved = learning.resolve_skill(skill)
    return {'algebra': 'Algebra', 'advanced_math': 'Advanced Math', 'data_analysis': 'Problem Solving and Data Analysis',
            'geometry': 'Geometry and Trigonometry', 'grammar': 'Standard English Conventions',
            'reading': 'Reading'}.get(resolved.get('domain'), resolved.get('subject', 'Test Strategy'))


def credit(track, skill):
    return JAMES_LU if track.startswith('sat') and skill in {'desmos_strategy', 'systems_of_equations', 'nonlinear_equations', 'quadratic_functions', 'boundaries', 'subject_verb_agreement', 'verb_tense', 'form_structure_sense'} else None


def item(skill, difficulty, prompt, options, answer, explanation, hints, *, source='', subskill=None, misconceptions=None):
    return {'skill_key': skill, 'subskill': subskill or skill, 'domain': domain(skill), 'difficulty': difficulty,
            'question_text': prompt, 'source_or_prompt': source, 'options': [str(x) for x in options],
            'correct_option': answer, 'explanation': explanation, 'hints': hints,
            'strategy': hints[1], 'fastest_method': hints[2],
            'misconceptions': misconceptions or ['Recheck the setup and requested quantity.' if i != answer else '' for i in range(4)],
            'validation': 'reviewed_bank'}


def shuffle_options(question, seed):
    # Legacy explanations can name a choice letter. Keep their reviewed order
    # rather than silently making that explanation incorrect.
    text = ' '.join(str(question.get(k,'')) for k in ('explanation','fastest_method','strategy','hints'))
    if re.search(r'\b(?:[Oo]ption|[Cc]hoice|[Aa]nswer)\s+[A-D]\b|\b[A-D]\s+(?:is|would|matches)\b',text):
        return dict(question)
    order = list(range(4))
    random.Random(seed).shuffle(order)
    result = dict(question)
    result['options'] = [question['options'][i] for i in order]
    result['correct_option'] = order.index(question['correct_option'])
    if len(question.get('misconceptions',[]))==4:
        result['misconceptions'] = [question['misconceptions'][i] for i in order]
    return result


def math_items(seed=0):
    n = 2 + seed % 17
    return [
        item('linear_equations_one', 'easy', f'If 3x + {n} = {7*n}, what is x?', [n, 2*n, 3*n, 6*n], 1,
             f'Subtract {n} from each side to obtain 3x = {6*n}; divide by 3 to obtain x = {2*n}. Substituting into the original equation checks the result. The value {6*n} stops before dividing by the coefficient.',
             ['First undo the addition.', 'Apply the same inverse operation to both sides.', 'After subtracting the constant, divide both sides by the coefficient of x.'], misconceptions=['Used the constant as the solution.', '', 'Did not isolate x.', 'Stopped before dividing by the coefficient.']),
        item('systems_of_equations', 'medium', f'The system x + y = {5*n} and 2x - y = {n} has a solution (x, y). What is y?', [n, 2*n, 3*n, 5*n], 2,
             f'Add the equations: 3x = {6*n}, so x = {2*n}. Substitute into the first equation: y = {5*n} - {2*n} = {3*n}. In a graphing calculator, graph both lines and read the y-coordinate of their intersection, not x.',
             ['Notice that the y terms have opposite signs.', 'Eliminate a variable by adding, or graph both equations and inspect their intersection.', 'After finding x, substitute into the first equation. The question asks for y.'], misconceptions=['Confused the second constant with y.', 'Answered x instead of y.', '', 'Used the total instead of one variable.']),
        item('linear_inequalities', 'hard', f'A club has ${10*n+7}. Renting a room costs $7 and each kit costs $3. What is the greatest whole number of kits the club can afford?', [10*n//3, 10*n//3+1, (10*n+7)//3, 10*n], 0,
             f'The cost constraint is 7 + 3k ≤ {10*n+7}. Subtract 7 to obtain 3k ≤ {10*n}. Thus k ≤ {10*n}/3. Round down because the number of kits is whole and the budget cannot be exceeded: {10*n//3}.',
             ['Separate the fixed cost from the per-kit cost.', 'Translate “can afford” into a less-than-or-equal-to inequality.', 'Subtract the room cost, divide by the per-kit cost, and round in the direction that stays within the budget.']),
        item('equivalent_expressions', 'easy', f'Which expression is equivalent to {n}(x + 4) - 2x?', [f'{n-2}x + 4', f'{n+2}x + {4*n}', f'{n}x + {4*n-2}', f'{n-2}x + {4*n}'], 3,
             f'Distributing gives {n}x + {4*n} - 2x. Combining the x terms gives {n-2}x + {4*n}. Distribution must apply to the constant as well as x; only like terms can be combined.',
             ['Distribute before combining.', 'Multiply every term inside the parentheses by the outside factor.', 'Group the x terms together and leave the constant separate.']),
        item('quadratic_functions', 'medium', f'The function f(x) = (x - {n})² + 3 has a minimum at (a, b). What is a + b?', [n, -3, n+3, -n-3], 2,
             f'A square is nonnegative, so the minimum occurs when x - {n} = 0. The vertex is ({n}, 3), giving a + b = {n+3}. Vertex form also makes the minimum easy to locate with Desmos. Reporting only one coordinate misses the requested sum.',
             ['Use the fact that a square cannot be negative.', 'In vertex form y = (x-h)²+k, the vertex is (h,k). You can confirm it by graphing.', 'Identify both vertex coordinates before adding them.']),
        item('exponential_functions', 'hard', f'A culture initially contains {100*n} cells and doubles every 3 hours. After how many hours will it contain {800*n} cells?', [3, 6, 9, 24], 2,
             f'The target is eight times the starting population: {800*n}/{100*n} = 8 = 2³. Three doublings are required. At 3 hours per doubling, the elapsed time is 3 × 3 = 9 hours. Doubling is multiplicative, not a constant increase.',
             ['Compare the final population with the initial population.', 'Express the growth factor as a power of 2 to count doublings.', 'Multiply the number of doublings by the time per doubling.']),
        item('percentages', 'easy', f'A ${20*n} jacket is discounted by 25%. What is the sale price?', [5*n, 15*n, 20*n, 25*n], 1,
             f'A 25% discount leaves 75% of the original price. Multiplying {20*n} by 0.75 gives {15*n}. The discount itself, {5*n}, is not the sale price; {20*n} ignores the discount, and {25*n} increases the price by 25%.',
             ['The sale price is the part of the price that remains.', 'Use a multiplier of 1 minus the discount rate.', 'Convert the percent to a decimal and multiply the original price by the retained fraction.']),
        item('probability', 'medium', f'A bag contains {n} red, {2*n} blue, and {n} green counters. One counter is chosen at random. What is the probability that it is blue?', ['1/4', '1/3', '1/2', '2/3'], 2,
             f'There are {4*n} counters in total and {2*n} are blue. The probability is {2*n}/{4*n} = 1/2. The denominator counts counters of all colors, not just the non-blue counters or the number of color categories.',
             ['Count favorable outcomes and all possible outcomes.', 'Probability is favorable equally likely outcomes divided by total outcomes.', 'Use the total number of counters as the denominator, then simplify.']),
        item('one_variable_data', 'hard', f'Five numbers have mean {4*n}. Four of them have sum {13*n}. What is the fifth number?', [n, 4*n, 7*n, 20*n], 2,
             f'The total of all five numbers is 5 × {4*n} = {20*n}. Subtracting the known sum, {13*n}, leaves {7*n}. An average is not the sum; convert it to a total before finding the missing value.',
             ['Turn the mean into a sum.', 'Total = mean × number of values.', 'Subtract the sum of the four known values from the total for all five.']),
        item('area_volume', 'easy', f'A rectangular box has length {n}, width 3, and height 4. What is its volume?', [7*n, 12*n, n+7, 24*n], 1,
             f'The volume of a rectangular prism is length × width × height. Here it is {n} × 3 × 4 = {12*n} cubic units. Adding dimensions does not compute volume; multiplying by 2 is unnecessary.',
             ['Volume measures three-dimensional space.', 'Multiply the three perpendicular dimensions.', 'Keep the answer in cubic units, not square units.']),
        item('right_triangles_trig', 'medium', f'A right triangle has legs of length {3*n} and {4*n}. What is its hypotenuse?', [n, 5*n, 7*n, 25*n*n], 1,
             f'By the Pythagorean theorem, c² = ({3*n})² + ({4*n})² = {25*n*n}. Taking the positive square root gives c = {5*n}. Recognizing a scaled 3–4–5 triangle gives the same result more quickly.',
             ['The unknown side is opposite the right angle.', 'Use a²+b²=c² or recognize a scaled 3–4–5 triangle.', 'If using the theorem, take the square root at the end.']),
        item('circles', 'hard', f'The circle x² + y² - {2*n}x + 6y + ({n*n-16}) = 0 has center (h,k) and radius r. What is h + k + r?', [n+8, n+2, n+22, -n-8], 1,
             f'Complete both squares: (x-{n})²+(y+3)²=25. Adding {n*n} and 9 to complete the squares gives the right side 25. In (x-h)²+(y-k)²=r², the center is ({n}, -3) and the radius is √25 = 5. Their sum is {n}-3+5 = {n+2}. The signs inside the parentheses are opposite the center coordinates; 25 is the radius squared.',
             ['First rewrite the equation in standard circle form.', 'Complete the square separately in x and y, keeping both sides balanced.', 'The completed-square constants are the squares of half the linear coefficients. Read the center and take the square root for the radius.']),
    ]


def ela_items():
    def e(skill, difficulty, source, prompt, options, answer, explanation, hints):
        return item(skill, difficulty, prompt, options, answer, explanation, hints, source=source)
    return [
        e('central_ideas','easy','A town converted an unused parking lot into a garden. Residents now grow vegetables there and meet each week to share tools and gardening advice.', 'Which choice best states the main idea?', ['A former parking lot now supports gardening and community interaction.','The town banned all parking.','Gardening tools are too expensive.','Residents no longer buy vegetables.'],0,'Both details—the vegetables and the weekly meetings—support a community garden serving multiple purposes. The other choices add claims about bans, costs, or shopping that the text never makes.',['Look for an answer covering the whole text.','Choose the claim supported by all major details, not an unsupported generalization.','Check both the food-growing detail and the meetings against each answer.']),
        e('command_of_evidence_text','medium','Researchers compared two otherwise similar groups of seedlings. After four weeks, the group receiving an extra hour of light each day was taller on average. The researchers cautioned that they had tested only one plant species.', 'Which conclusion is most directly supported?', ['Extra light benefits every species.','The extra-light group grew taller on average under the tested conditions.','All plants require exactly one extra hour of light.','Light was the only possible influence on growth in nature.'],1,'The reported result concerns the groups and conditions in this experiment. The stated species limitation rules out universal conclusions. No exact requirement for all plants or claim about every influence in nature is established.',['Identify exactly what was measured.','Limit the conclusion to the evidence and population described.','Eliminate choices using universal claims the researchers explicitly caution against.']),
        e('inferences','hard','A historian found several early drafts of a speech with detailed economic arguments. In the delivered version, those arguments were replaced by short accounts of workers’ daily lives. The speech retained the same policy proposal.', 'Which inference is best supported?', ['The speaker abandoned the policy.','The early drafts were written after the speech.','The speaker changed the way the policy was presented while retaining its substance.','The delivered speech contained more economic detail.'],2,'The presentation changed from detailed economic arguments to personal accounts, while the proposal stayed the same. That supports a change in framing, not abandonment or reversal of the policy. The text establishes no reversed drafting chronology.',['Separate what changed from what stayed the same.','An inference should connect stated details without adding unsupported motives.','Compare the presentation style across versions and the unchanged proposal.']),
        e('words_in_context','easy','Although the instrument appeared fragile, it proved remarkably resilient, continuing to function after repeated exposure to extreme temperatures.', 'As used in the text, “resilient” most nearly means:', ['delicate','ornamental','costly','durable'],3,'Continuing to function despite harsh temperatures shows durability. Although signals a contrast with fragile, ruling out delicate. Nothing in the passage establishes the instrument’s price or decorative purpose.',['Use the contrast signaled by “although.”','Predict a plain-language meaning before comparing options.','The instrument kept working despite harsh conditions.']),
        e('text_structure_purpose','medium','The essay first describes an abandoned railway station with broken windows and empty platforms. It then recounts the station’s earlier role as a busy meeting place for travelers and merchants.', 'What is the main purpose of the description of the station’s earlier role?', ['To explain how train engines operate','To contrast its former activity with its current disuse','To recommend a travel itinerary','To prove the station was never popular'],1,'The earlier bustle contrasts with the present abandonment. The description develops that contrast rather than explaining machinery, advising travel, or denying the past popularity it explicitly describes.',['Notice the change in time period.','Ask what the detail does in the passage, rather than just what it says.','Compare the empty present-day station with the busy earlier station.']),
        e('cross_text_connections','hard','Text 1: Urban trees can cool streets through shade and evaporation. Therefore, expanding tree cover can reduce summer heat in cities.\nText 2: Urban trees provide cooling, but planting choices matter: species poorly suited to local conditions may require substantial water and maintenance.', 'How would the author of Text 2 most likely respond to Text 1?', ['By denying that trees provide cooling','By claiming all tree species require identical care','By agreeing about cooling while emphasizing a condition for effective planting','By arguing that cities should remove existing trees'],2,'Text 2 explicitly accepts cooling, then qualifies implementation with species selection and resource needs. Agreement with a qualification captures both parts. Denial, identical care, and removal contradict or exceed the text.',['Find the point both texts accept.','Distinguish disagreement from agreement with a qualification.','Look for an option that includes both cooling and the need to choose suitable species.']),
        e('transitions','easy','The new pump uses less electricity than the old model. _____, the laboratory’s energy bill has decreased.', 'Which choice completes the text with the most logical transition?', ['Nevertheless','Consequently','For example','Instead'],1,'Lower electricity use leads to a lower bill, so consequently expresses the result. Nevertheless and instead imply contrast or replacement; for example would introduce an illustration rather than this consequence.',['Name the relationship between the two sentences.','Choose a transition by logic, not by how smooth it sounds.','The second sentence describes a result of the first.']),
        e('rhetorical_synthesis','medium','Notes:\n- Researcher A studied birds in coastal wetlands.\n- Researcher B studied birds in mountain forests.\n- Both studies recorded seasonal migration patterns.', 'The student wants to emphasize a difference between the studies. Which choice best accomplishes this?', ['Both researchers studied seasonal migration.','Both studies involved birds.','Researcher A studied coastal wetlands, whereas Researcher B studied mountain forests.','Migration patterns can vary by season.'],2,'The requested goal is a difference, and the settings differ. The correct choice directly contrasts those settings. Two choices describe similarities; the general statement about variation does not compare the actual studies.',['Read the student’s goal first.','Use only notes that serve the requested rhetorical purpose.','Compare the locations rather than the shared topic.']),
        e('transitions','hard','Early tests suggested that the coating would resist saltwater damage. Longer trials revealed substantial corrosion. _____, the team revised its initial conclusion.', 'Which choice completes the text with the most logical transition?', ['Accordingly','Similarly','For instance','Nevertheless'],0,'The revision follows as a consequence of the new evidence, so accordingly fits. The contrast between early and longer trials has already been established; the blank connects that evidence to the team’s response, not one trial to the other.',['Look at the sentences immediately around the blank.','Identify what the transition connects: evidence to a response, or two findings to each other.','The revised conclusion follows from the longer trials.']),
        e('boundaries','easy','The archive opened in June _____ researchers can now examine its letters online.', 'Which choice completes the text so that it conforms to the conventions of Standard English?', [',',';','because of','with'],1,'Both sides are independent clauses, so a semicolon joins them correctly. A comma alone creates a comma splice. Because of and with cannot connect these complete clauses in this construction.',['Check whether each side is a complete sentence.','A period or semicolon can separate two independent clauses; a comma alone cannot.','Find the subject and finite verb on both sides of the blank.']),
        e('subject_verb_agreement','medium','The collection of letters from several explorers _____ a detailed account of the expedition.', 'Which choice completes the text so that it conforms to the conventions of Standard English?', ['provide','have provided','are providing','provides'],3,'The grammatical subject is the singular collection, not the plural letters or explorers. Provides agrees with the singular subject. Each other option uses a plural verb form.',['Find the grammatical subject.','Ignore nouns inside intervening prepositional phrases when matching subject and verb.','Temporarily remove “of letters from several explorers” and read the core sentence.']),
        e('verb_tense','hard','By the time the museum opened in 2020, the conservators _____ the restoration, which they had begun three years earlier.', 'Which choice completes the text so that it conforms to the conventions of Standard English?', ['will complete','have completed','had completed','are completing'],2,'The restoration was complete before another past event, the museum opening. Had completed marks that earlier past action. Present-perfect, present-progressive, and future forms conflict with the stated sequence.',['Put the two events on a timeline.','Use past perfect for an action completed before another past event.','The restoration was already finished when the museum opened.']),
    ]


def bank(track, seed=0):
    questions = math_items(seed) if track.endswith('math') else ela_items()
    if track.startswith('act'):
        mapping = {'algebra': 'act_math_prealgebra', 'advanced_math': 'act_math_coordinate',
                   'data_analysis': 'act_math_prealgebra', 'geometry': 'act_math_plane_geometry'}
        for q in questions:
            original = q['skill_key']
            resolved = learning.resolve_skill(original)
            if track.endswith('math'):
                key = 'act_math_trig' if original == 'right_triangles_trig' else mapping.get(resolved.get('domain'), 'act_math_prealgebra')
            else:
                key = 'act_english_usage' if original in {'boundaries','subject_verb_agreement','verb_tense'} else 'act_english_rhetoric' if original in {'transitions','rhetorical_synthesis'} else 'act_reading_detail'
            q['skill_key'] = key
            q['subskill'] = original
    for q in questions:
        q['attribution'] = credit(track, q['skill_key'])
    return [shuffle_options(q,seed*101+i*17) for i,q in enumerate(questions)]
