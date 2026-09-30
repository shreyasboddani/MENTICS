"""ACT English benchmark: five passages, ten questions each (questions 1-50).

Underlined portions appear in the passage as [underlined N: text]. Answer order
is fixed (NO CHANGE first), as on the test, so the bank does not shuffle them.
"""

USAGE, RHET = 'act_english_usage', 'act_english_rhetoric'
STEM = 'Which choice is the best version of the underlined portion? If the original is best, choose “NO CHANGE.”'

HINTS = {
    USAGE: ['Read the sentence with the underlined portion and decide what grammar rule is being tested.',
            'Check agreement, punctuation, tense and parallel structure before judging how the choice sounds.',
            'Substitute each choice into the full sentence; eliminate any that create a new error.'],
    RHET: ['Decide what the question is really asking: concision, logic, purpose, or tone.',
           'The best choice serves the writer’s goal and adds no redundancy or off-topic detail.',
           'Reread the surrounding sentences; choose what fits the paragraph’s point.'],
}
NOTES = {USAGE: ['Keeps the original error.', 'Creates a different grammar or punctuation error.', 'Changes the meaning or structure incorrectly.'],
         RHET: ['Keeps the original wording problem.', 'Is wordy, vague or off-topic.', 'Does not serve the writer’s goal.']}


def Q(n, skill, diff, sub, options, answer, why, stem=None):
    hints = HINTS[skill]
    notes = [NOTES[skill][i % 3] if i != answer else '' for i in range(4)]
    return {'skill_key': skill, 'subskill': sub, 'difficulty': diff, 'module': 1, 'number': n,
            'question_text': f'Question {n}. {stem or STEM}', 'options': options, 'correct_option': answer,
            'explanation': why, 'hints': hints, 'strategy': hints[1], 'fastest_method': hints[2],
            'misconceptions': notes, 'validation': 'reviewed_bank', 'fixed_order': True}


NC = 'NO CHANGE'

P1 = """When the Halsey Street Community Garden opened in 2009, it was little more than a vacant lot [underlined 1: filled with broken bricks, it had weeds, and rusted scrap metal]. Neighbors who walked past it each day [underlined 2: has learned] to look away. Then Denise Okoro, a retired school nurse, began hauling away the debris one wheelbarrow at a time [underlined 3: ; because] she could not bear to see good soil wasted.

Within a month, [underlined 4: a dozen volunteers joined her, they] brought shovels, seeds, and secondhand fencing donated by a hardware store. By spring, the lot had been divided into thirty raised beds, [underlined 5: each one of which were] rented to a nearby household for ten dollars a season. [underlined 6: The gardens crops] ranged from tomatoes and collard greens to peppers that surprised even experienced growers with their heat.

Keeping the garden productive, however, required more than enthusiasm. Okoro discovered that the soil, [underlined 7: which had been compacted by decades of disuse] needed compost, and that the compost needed a steady supply of kitchen scraps. She [underlined 8: persuaded the owner of a nearby restaurant to donate them every Friday on a weekly basis]. [underlined 9: Gardeners learned to balance green scraps, such as vegetable peels, with brown ones, such as dry leaves.] That mixture, left to decompose for a few months, turned into the dark, crumbly compost that the beds required.

[underlined 10: Today, the garden supplies fresh produce to a food pantry two blocks away, and the vacant lot that neighbors once avoided has become the place where they gather.]"""

Q1 = [
    Q(1, USAGE, 'medium', 'parallel structure', [NC, 'filled with broken bricks, weeds, and rusted scrap metal', 'filled with broken bricks, having weeds, and rusted scrap metal', 'filled with broken bricks and it had weeds, and rusted scrap metal'], 1, 'The items in the list must be parallel nouns: bricks, weeds, and scrap metal. The original inserts a clause (“it had weeds”) in the middle of the series.'),
    Q(2, USAGE, 'easy', 'verb tense', [NC, 'had learned', 'learns', 'will learn'], 1, 'The sentence describes neighbors who “walked” past in the past, before the garden existed, so the past perfect “had learned” is correct.'),
    Q(3, USAGE, 'medium', 'punctuation with subordinating conjunctions', [NC, ', because', '. Because', ': because'], 1, '“Because she could not bear to see good soil wasted” is a dependent clause that completes the sentence; it takes a comma, not a semicolon, period, or colon.'),
    Q(4, USAGE, 'medium', 'comma splice', [NC, 'a dozen volunteers joined her; they', 'a dozen volunteers joining her, they', 'a dozen volunteers joined her they'], 1, 'The original joins two independent clauses with only a comma. A semicolon correctly joins them. The other choices create a fragment or a run-on.'),
    Q(5, USAGE, 'medium', 'subject-verb agreement', [NC, 'each of which was', 'each of them were', 'each one, which were'], 1, '“Each” is singular, so the verb must be “was.” “Each of which was” also removes the wordiness of “each one of which.”'),
    Q(6, USAGE, 'easy', 'possessive apostrophes', [NC, 'The garden’s crops', 'The gardens’ crops', 'The garden, crops'], 1, 'The crops belong to a single garden, so the singular possessive “garden’s” is required.'),
    Q(7, USAGE, 'medium', 'nonessential clauses', [NC, 'which had been compacted by decades of disuse,', 'which had been compacted, by decades of disuse', 'that had been compacted by decades of disuse,'], 1, 'The clause is nonessential and began after a comma, so it must end with a comma. “That” cannot introduce a clause set off by commas.'),
    Q(8, RHET, 'easy', 'concision', [NC, 'persuaded the owner of a nearby restaurant to donate them every Friday', 'persuaded the owner of a nearby restaurant to donate them weekly every Friday', 'persuaded the owner of a nearby restaurant to be donating them on each and every Friday'], 1, '“Every Friday” already means weekly, so “on a weekly basis” is redundant. The concise version is best.'),
    Q(9, RHET, 'medium', 'add or delete a sentence', ['Kept, because it explains what the two kinds of scraps are, helping readers understand how the compost mixture is made.', 'Kept, because it shows that Okoro disagreed with the other gardeners about composting.', 'Deleted, because it introduces a detail that is unrelated to the garden’s compost.', 'Deleted, because it repeats information given earlier in the essay.'], 0, 'The next sentence refers to “that mixture,” which the underlined sentence defines. It is relevant, clear, and not repeated elsewhere.', stem='The writer is considering deleting the underlined sentence. Should the sentence be kept or deleted?'),
    Q(10, RHET, 'medium', 'effective conclusion', [NC, 'The garden also gives Okoro something to do during her retirement.', 'Gardening is a popular hobby in many cities across the country.', 'Hardware stores in the area still donate supplies to the garden.'], 0, 'The original closes the essay by contrasting the lot’s past with its present role in the community. The other choices shift to unrelated or minor points.', stem='Which choice most effectively concludes the essay by emphasizing the transformation of the lot?'),
]

P2 = """In the 1870s, the most common bicycle in Europe was the high-wheeler, a machine with an enormous front wheel and a tiny rear one. Riders sat nearly five feet above the ground, [underlined 11: which meant that when a rider fell, the falling that resulted was often quite a serious one]. Most riders were young men willing to accept the risk, and [underlined 12: the high-wheeler, remained a curiosity] to everyone else.

That changed in 1885, when English inventor John Kemp Starley introduced the Rover, [underlined 13: a thing for riding]. Sitting low to the ground, [underlined 14: the Rover seemed far safer than the high-wheeler]. [underlined 15: It’s] design proved so sound that bicycles today still follow its basic layout.

The safety bicycle soon found an eager audience among women, [underlined 16: whom had been excluded from high-wheel riding by their clothing and by social convention]. For many women, cycling offered an unprecedented means of independent travel, and cycling clubs formed in cities from Boston to Berlin. [underlined 17: Consequently,] some doctors warned that the exercise would harm women’s health, but the evidence they offered was thin.

By the 1890s, millions of people [underlined 18: ride] bicycles to work, to school, and to visit friends in neighboring towns. The craze led road builders to demand smoother pavement, which later benefited automobile drivers as well. [underlined 19: Bicycles were made of metal and rubber.]"""

Q2 = [
    Q(11, RHET, 'medium', 'concision', [NC, 'so falls were often serious', 'meaning that a fall, when one occurred, was often of a serious nature', 'which is why any fall, if a rider happened to fall, could often be serious'], 1, 'The original repeats “fell” and “falling.” “So falls were often serious” says the same thing directly.'),
    Q(12, USAGE, 'easy', 'unnecessary commas', [NC, 'the high-wheeler remained a curiosity', 'the high-wheeler; remained a curiosity', 'the high-wheeler remained, a curiosity'], 1, 'No punctuation should separate a subject from its verb. The correct version has none.'),
    Q(13, RHET, 'medium', 'precise detail', [NC, 'a bicycle with two wheels of equal size and a chain that drove the rear wheel', 'an invention that many people found interesting', 'something for riding'], 1, 'The essay contrasts the Rover with the high-wheeler, so the most relevant detail is its equal-sized wheels and chain drive. The others are vague.', stem='Which choice provides the most relevant and specific information at this point in the essay?'),
    Q(14, USAGE, 'hard', 'dangling modifiers', [NC, 'riders found the Rover far safer than the high-wheeler', 'safety came with the Rover, far safer than the high-wheeler', 'a far safer bicycle than the high-wheeler was the Rover'], 1, '“Sitting low to the ground” must modify the riders, not the Rover. Only the choice that names riders immediately after the comma fixes this.'),
    Q(15, USAGE, 'easy', 'its versus it’s', [NC, 'Its', 'Their', 'Its’'], 1, 'The possessive pronoun “its” modifies “design.” “It’s” is a contraction meaning “it is,” and “their” would not agree with the singular “bicycle.”'),
    Q(16, USAGE, 'medium', 'who versus whom', [NC, 'who', 'which', 'whose'], 1, '“Who” is the subject of “had been excluded” and refers to women. “Whom” is for objects, and “which” is for things.'),
    Q(17, RHET, 'medium', 'transitions', [NC, 'However,', 'Similarly,', 'For example,'], 1, 'Doctors’ warnings stand in contrast to women’s enthusiasm for cycling, and the sentence continues with “but the evidence was thin.” “Consequently” implies the clubs caused the warnings.', stem='Which choice provides the most logical transition between the ideas in the two sentences?'),
    Q(18, USAGE, 'easy', 'verb tense consistency', [NC, 'rode', 'will ride', 'are riding'], 1, '“By the 1890s” places the action in the past, so the past tense “rode” is required.'),
    Q(19, RHET, 'medium', 'effective conclusion', [NC, 'In short, the safety bicycle turned a dangerous novelty into a practical tool that reshaped ordinary people’s lives.', 'Many people today ride bicycles for exercise rather than for transportation.', 'Starley’s company eventually stopped making bicycles.'], 1, 'The essay’s main point is that the safety bicycle made travel safe and accessible. Only the sentence about the bicycle reshaping ordinary people’s lives reinforces it.', stem='The writer wants to conclude the essay with a sentence that reinforces its main point. Which choice best accomplishes that goal?'),
    Q(20, RHET, 'medium', 'whole-essay purpose', ['Yes, because it describes how the safety bicycle let more people, including women, travel independently.', 'Yes, because it explains in detail how a bicycle’s chain and wheels function.', 'No, because it focuses on the history of the high-wheeler rather than on the safety bicycle.', 'No, because it does not mention any effects of the invention beyond the 1880s.'], 0, 'The essay shows how a technological change broadened access to travel, which is the stated goal. It does mention effects after the 1880s.', stem='Suppose the writer’s goal had been to explain how a technological invention expanded ordinary people’s access to travel. Would this essay accomplish that goal?'),
]

P3 = """For most of human history, the floor of the ocean was [underlined 21: a mystery, no one knew] what lay beneath the waves. Early sailors measured depth by lowering weighted ropes, a slow method that produced only a handful of readings on a single voyage. In the 1920s, ships began using [underlined 22: sonar—a technique that bounces sound waves off the seafloor and measures the time the echoes take to return]. [underlined 23: Despite this,] researchers could finally chart mountains, trenches, and ridges that no one had ever seen.

Today, Dr. Amara Nwosu, [underlined 24: which] leads a mapping team at a coastal research institute, uses sonar arrays towed behind ships. Her team [underlined 25: have mapped] a stretch of seafloor roughly the size of Wales. The maps reveal hidden features such as underwater volcanoes[underlined 26: , submerged beneath the surface of the water,] and canyons deeper than any on land. [underlined 27: Submarines have also used sonar since the early twentieth century.]

The maps matter for reasons beyond curiosity. They help scientists understand [underlined 28: how ocean currents are affected from the shape of the seafloor]. Currents that flow over a ridge [underlined 29: mixed] heat and nutrients differently than currents over open plains, and those differences influence where fish gather and how quickly the ocean absorbs heat from the atmosphere. [underlined 30: Nwosu’s work is ongoing.]"""

Q3 = [
    Q(21, USAGE, 'medium', 'comma splice', [NC, 'a mystery because no one knew', 'a mystery, no one having known', 'a mystery; and no one knew'], 1, 'The original splices two independent clauses with a comma. “Because” subordinates the second clause correctly.'),
    Q(22, USAGE, 'medium', 'dashes and appositives', [NC, 'sonar, a technique that bounces sound waves off the seafloor, and measures the time the echoes take to return', 'sonar: a technique, that bounces sound waves off the seafloor and measures the time the echoes take to return', 'sonar a technique that bounces sound waves off the seafloor and measures the time the echoes take to return'], 0, 'The dash correctly introduces an explanatory phrase. The alternatives add a stray comma, break the phrase, or remove the punctuation entirely.'),
    Q(23, RHET, 'medium', 'transitions', [NC, 'With it,', 'In contrast,', 'Even so,'], 1, 'Sonar made charting possible, so “With it” connects cause and effect. “Despite this” implies sonar was an obstacle.', stem='Which choice most logically connects this sentence to the one before it?'),
    Q(24, USAGE, 'easy', 'who versus which', [NC, 'who', 'whom', 'that'], 1, 'The clause describes a person, Dr. Nwosu, and serves as the subject of “leads,” so it needs the subject pronoun “who.” “Which” is used for things.'),
    Q(25, USAGE, 'easy', 'subject-verb agreement', [NC, 'has mapped', 'are mapping', 'were to map'], 1, '“Team” is a singular collective noun here, so the verb must be the singular “has mapped.” “Have” and “are” are plural forms.'),
    Q(26, RHET, 'medium', 'redundancy', [NC, 'OMIT the underlined portion.', ', hidden under the ocean’s surface,', ', lying below the water’s surface,'], 1, '“Underwater” already says the volcanoes are beneath the surface, so every version of the phrase is redundant. Omitting it is best.', stem='Which choice is best? If it is best to omit the underlined portion, choose “OMIT the underlined portion.”'),
    Q(27, RHET, 'medium', 'add or delete a sentence', ['Kept, because it provides another example of the benefits of sonar mapping.', 'Kept, because it explains how sonar arrays are towed behind ships.', 'Deleted, because it shifts the focus from mapping the seafloor to an unrelated use of sonar.', 'Deleted, because it contradicts the claim that sonar was first used in the 1920s.'], 2, 'The paragraph is about what seafloor maps reveal; a sentence about submarines digresses.', stem='The writer is considering deleting the underlined sentence. Should the sentence be kept or deleted?'),
    Q(28, USAGE, 'medium', 'idiom and prepositions', [NC, 'how ocean currents are affected by the shape of the seafloor', 'how ocean currents are affecting of the shape of the seafloor', 'how the shape of the seafloor is affected from ocean currents'], 1, 'Things are “affected by” their causes, and the context says the shape of the seafloor influences currents.'),
    Q(29, USAGE, 'easy', 'verb tense consistency', [NC, 'mix', 'had mixed', 'will have mixed'], 1, 'The passage describes ongoing general facts in the present tense, so “mix” is consistent.'),
    Q(30, RHET, 'medium', 'effective conclusion', [NC, 'Better maps of the seafloor may help scientists predict how the ocean will respond as the climate changes.', 'Nwosu has worked at the institute for many years.', 'Wales is about 20,000 square kilometers in area.'], 1, 'The paragraph argues that the maps matter for understanding ocean heat and currents; the sentence about predicting the ocean’s response to climate change extends that point. The others add unrelated facts.', stem='Which choice most effectively concludes the essay by emphasizing why the maps matter?'),
]

P4 = """My grandmother’s kitchen was small, but it held everything she thought a person needed. She kept three things on the counter [underlined 31: ; a radio, a jar of dried chilies, and a cracked blue bowl] that she had carried across an ocean. On the night the storm knocked out power to our whole street, we were all crowded in there, waiting for the lights to return.

[underlined 32: My grandmothers hands] were the first thing I noticed in the glow of the first match, steady as always while the rest of us fumbled. When the power [underlined 33: goes] out that night, she did not sigh or complain; she lit candles and set them along the windowsill. My cousin Ravi and my brother argued about whether [underlined 34: he] had left the flashlight in the car. Grandmother ignored the argument and [underlined 35: threw] a candle to each of us.

She used the dark as an excuse to teach. She taught us how to knead dough, how to tell when it was ready, and [underlined 36: to bake it without a recipe]. [underlined 37: Therefore,] when the power returned hours later, nobody moved to switch on the lamps. [underlined 38: We all just sat there, sitting quietly,] eating warm bread while the storm faded. The kitchen was warm[underlined 39: , however it smelled of smoke and dough], and I remember wishing the night would last."""

Q4 = [
    Q(31, USAGE, 'medium', 'colons', [NC, ': a radio, a jar of dried chilies, and a cracked blue bowl', ', a radio, a jar of dried chilies, and a cracked blue bowl', '; which were a radio, a jar of dried chilies, and a cracked blue bowl'], 1, 'A colon can follow a complete clause to introduce a list. A semicolon requires a complete clause afterward.'),
    Q(32, USAGE, 'easy', 'possessive apostrophes', [NC, 'My grandmother’s hands', 'My grandmothers’ hands', 'My grandmother hands'], 1, 'The hands belong to one grandmother, so the singular possessive is correct.'),
    Q(33, USAGE, 'easy', 'verb tense consistency', [NC, 'went', 'has gone', 'will go'], 1, 'The narrator describes a past evening, so the past tense “went” is required.'),
    Q(34, USAGE, 'medium', 'pronoun clarity', [NC, 'Ravi', 'they', 'that person'], 1, '“He” could refer to either the cousin or the brother. Naming Ravi makes the reference clear.'),
    Q(35, RHET, 'medium', 'tone and word choice', [NC, 'handed', 'hurled', 'flung'], 1, 'The scene is calm and affectionate, so “handed” fits. “Threw,” “hurled,” and “flung” suggest harshness and risk with a lit candle.', stem='Which choice best maintains the calm, affectionate tone of the paragraph?'),
    Q(36, USAGE, 'medium', 'parallel structure', [NC, 'how to bake it without a recipe', 'baking it without a recipe', 'that we should bake it without a recipe'], 1, 'The series repeats “how to knead… how to tell…,” so the last item must be “how to bake.”'),
    Q(37, RHET, 'medium', 'transitions', [NC, 'Finally,', 'For example,', 'Instead,'], 1, 'The sentence moves forward in time to the return of power. “Therefore” falsely implies a cause.', stem='Which choice provides the most logical transition at this point in the paragraph?'),
    Q(38, RHET, 'easy', 'redundancy', [NC, 'We all sat quietly,', 'We all just sat there in a state of quiet sitting,', 'All of us there were sitting quietly in place,'], 1, 'The original says “sat” and “sitting” together; the concise version removes the redundancy.'),
    Q(39, USAGE, 'hard', 'conjunctive adverbs', [NC, '; however, it smelled of smoke and dough', 'however, it smelled of smoke and dough', ', however, it smelled of smoke and dough'], 1, '“However” between two independent clauses needs a semicolon before it and a comma after it. A comma alone makes a comma splice.'),
    Q(40, RHET, 'medium', 'whole-essay purpose', ['Yes, because it describes a specific evening and conveys what the evening meant to the narrator.', 'Yes, because it explains in detail how to bake bread.', 'No, because it focuses on the narrator’s brother rather than on the grandmother.', 'No, because it contains too many details about the storm.'], 0, 'The essay recounts a particular night with the narrator’s grandmother and what it meant to the narrator, which fits a brief personal essay on a family memory.', stem='Suppose the writer’s goal had been to write a brief personal essay about a meaningful family memory. Would this essay fulfill that goal?'),
]

P5 = """Walk into a public library today and you may not hear the hush that once defined such places. In many cities, libraries have become [underlined 41: busy, lively, and they are welcoming] community centers where residents [underlined 42: borrows] tools, attend job workshops, and apply for benefits. Librarians say the change reflects what patrons actually need.

[underlined 43: For example,] the library in Dunmore, a mid-sized town in Ohio, lends more than just books. Its catalog includes power drills, sewing machines, and [underlined 44: telescope’s] that residents can reserve for a week at a time. Staff members also run a weekly clinic where volunteers help people complete tax forms[underlined 45: , a service that helps to save many families a good deal of money that they would otherwise have to spend on a professional preparer].

Not everyone welcomed the shift. Some longtime patrons worried that [underlined 46: there] quiet reading rooms would disappear. Dunmore’s head librarian, Carmen Delgado, responded by setting aside two floors for silent study[underlined 47: , while, reserving the ground floor for activity]. Attendance has [underlined 48: rose] by nearly forty percent since the changes began.

The changes have come with costs. Budgets have not kept pace with the new services, and staff members often work evenings. [underlined 49: Therefore,] Delgado insists that the library’s mission has not changed: it exists to give every resident access to information and opportunity. The tools and the clinics, she says, are simply new ways of doing an old job."""

Q5 = [
    Q(41, USAGE, 'medium', 'parallel structure', [NC, 'busy, lively, and welcoming', 'busy and lively, they are welcoming', 'busy, being lively, and welcoming'], 1, 'A series of adjectives must stay parallel: busy, lively, welcoming. The original breaks the pattern by inserting a full clause (“they are welcoming”).'),
    Q(42, USAGE, 'easy', 'subject-verb agreement', [NC, 'borrow', 'borrowing', 'has borrowed'], 1, '“Residents” is plural, so the plural verb “borrow” is required and matches “attend” and “apply.”'),
    Q(43, RHET, 'easy', 'transitions', [NC, 'In contrast,', 'Regardless,', 'Consequently,'], 0, 'The paragraph gives a specific example of the general change described before, so “For example” is correct.', stem='Which choice most logically introduces the paragraph? (If the original is best, choose “NO CHANGE.”)'),
    Q(44, USAGE, 'easy', 'plurals versus possessives', [NC, 'telescopes', 'telescopes’', 'telescope'], 1, 'The list needs a plain plural noun, “telescopes.” An apostrophe is unnecessary.'),
    Q(45, RHET, 'medium', 'concision', [NC, ', a service that saves families the cost of a professional preparer', ', which is a service that helps to save many families a good deal of the money they would otherwise spend', ', saving money for families that would otherwise have been spent'], 1, 'The concise version keeps the meaning without the filler in the original.'),
    Q(46, USAGE, 'easy', 'their, there, they’re', [NC, 'their', 'they’re', 'its'], 1, 'The possessive “their” shows that the reading rooms belong to the patrons. “There” points to a place and “they’re” means “they are.”'),
    Q(47, USAGE, 'medium', 'unnecessary commas', [NC, ', while reserving the ground floor for activity', '; while, reserving the ground floor for activity', ' while, reserving the ground floor for activity'], 1, 'The phrase “while reserving…” needs one comma before it and none after “while.”'),
    Q(48, USAGE, 'medium', 'irregular verb forms', [NC, 'risen', 'raised', 'rised'], 1, '“Has risen” is the present perfect of the intransitive verb “rise.” “Raised” requires an object.'),
    Q(49, RHET, 'medium', 'transitions', [NC, 'Nevertheless,', 'Similarly,', 'For example,'], 1, 'Delgado’s insistence contrasts with the difficulties just described. “Nevertheless” signals that contrast.', stem='Which choice provides the most logical transition between the two sentences?'),
    Q(50, RHET, 'medium', 'whole-essay purpose', ['Yes, because it shows how one library has changed to meet residents’ needs.', 'Yes, because it compares libraries in several different countries.', 'No, because it never mentions what the library offers to residents.', 'No, because it focuses on the history of library architecture.'], 0, 'The essay traces how the Dunmore library and others have expanded their services for residents.', stem='Suppose the writer’s goal had been to explain how one public library has adapted to serve its community. Would this essay accomplish that goal?'),
]

PASSAGES = [(P1, Q1), (P2, Q2), (P3, Q3), (P4, Q4), (P5, Q5)]


def english_items():
    items = []
    for text, questions in PASSAGES:
        for q in questions:
            item = dict(q)
            item['source_or_prompt'] = text
            items.append(item)
    return items
