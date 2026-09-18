"""Original ACT Arena reserve items, used when live generation is unavailable.

Arena rounds are short, mixed-section challenges, not ACT score predictions.
Each set contains three Math items, one Reading item, and one English item.
"""
import random


def fallback_questions(difficulty):
    rng = random.SystemRandom()
    tiers = ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'grandmaster']
    level = tiers.index(difficulty)
    n = rng.randint(3, 9)

    def math(stem, answer, distractors, skill, explanation):
        return dict(question_text=stem, options=[str(answer), *map(str, distractors)], correct_option=0,
                    domain='math', section='Math', skill=f'ACT Math: {skill}', explanation=explanation)

    if level == 0:
        questions = [
            math(f'A club pays a fixed delivery fee of ${n} plus $4 for each notebook. The total bill is ${n + 28}. How many notebooks did the club order?', 7, [6, 8, n + 7], 'Linear models', f'Subtract the fixed fee of ${n} from ${n + 28}, leaving $28 for notebooks. Each notebook costs $4, so the order contains 28 / 4 = 7 notebooks.'),
            math(f'A cyclist travels {n * 12} kilometers in 3 hours at a constant speed. At the same speed, how many kilometers will the cyclist travel in 5 hours?', n * 20, [n * 4, n * 12 + 2, n * 60], 'Proportional reasoning', f'The speed is {n * 12} / 3 = {n * 4} kilometers per hour. Multiply by 5 hours to get {n * 20} kilometers. Adding 2 to the distance would confuse hours with kilometers.'),
            math(f'A rectangular garden is {n} meters wide and {n + 4} meters long. What is its perimeter, in meters?', 4 * n + 8, [n * (n + 4), 2 * n + 4, 4 * n + 4], 'Perimeter', f'The perimeter includes two widths and two lengths: 2({n}) + 2({n + 4}) = {4 * n + 8}. Multiplying the side lengths gives area, not perimeter.'),
        ]
    elif level == 1:
        questions = [
            math(f'A jacket originally costs ${20 * n}. It is discounted by 20%, and then a 10% tax is applied to the discounted price. What is the final cost in dollars?', f'{17.6 * n:.2f}', [f'{18 * n:.2f}', f'{22 * n:.2f}', f'{16 * n:.2f}'], 'Successive percentages', f'Apply the discount first, then the tax: {20 * n} x 0.80 x 1.10 = {17.6 * n:.2f}. The tax is on the reduced price, so subtracting 20% and adding 10% of the original price is incorrect.'),
            math(f'A line passes through (2, {n + 6}) and (5, {n + 15}). What is the y-intercept of the line?', n, [n - 1, n + 3, n + 6], 'Coordinate geometry', f'The slope is ({n + 15} - {n + 6}) / (5 - 2) = 3. Substitute (2, {n + 6}) into y = 3x + b to get b = {n}.'),
            math(f'The average of five numbers is {n + 8}. Four of the numbers are {n}, {n + 2}, {n + 4}, and {n + 6}. What is the fifth number?', n + 28, [n + 8, n + 20, n + 40], 'Means and totals', f'The total must be 5({n + 8}) = {5 * (n + 8)}. The known values sum to {4 * n + 12}, so the missing value is {n + 28}.'),
        ]
    elif level == 2:
        questions = [
            math(f'The roots of x^2 - {2 * n + 3}x + {n * (n + 3)} = 0 are r and s, where r < s. What is 2r + s?', 3 * n + 3, [2 * n + 3, 3 * n + 6, n * (n + 3)], 'Quadratic roots', f'The polynomial factors as (x - {n})(x - {n + 3}). Thus r = {n} and s = {n + 3}, giving 2r + s = {3 * n + 3}.'),
            math(f'A bag contains {n} red marbles and {2 * n} blue marbles. Two marbles are drawn without replacement. What is the probability both are red?', f'{n - 1}/{3 * (3 * n - 1)}', ['1/9', '1/3', f'{n}/{3 * n - 1}'], 'Dependent probability', f'The first red probability is 1/3. After drawing red, {n - 1} red marbles remain among {3 * n - 1} total marbles. Multiply to obtain ({n - 1}) / ({3 * (3 * n - 1)}).'),
            math(f'A right triangle has legs of lengths {3 * n} and {4 * n}. What is the sine of the angle opposite the shorter leg?', '3/5', ['4/5', '3/4', '5/3'], 'Right-triangle trigonometry', f'The hypotenuse is {5 * n} by the Pythagorean theorem. Sine is opposite over hypotenuse, so the answer is {3 * n}/{5 * n} = 3/5, not the opposite-over-adjacent ratio.'),
        ]
    elif level == 3:
        questions = [
            math(f'Let f(x) = 2x - {n} and g(x) = x^2 + 1. What is the positive solution of g(f(x)) = 26?', f'{n + 5}/2', [f'{n + 26}/2', f'{n + 1}/2', f'{n - 5}/2'], 'Function composition', f'Composition gives (2x - {n})^2 + 1 = 26. Thus 2x - {n} = 5 or -5. The larger solution is ({n + 5})/2. This question asks for the positive solution only when the other root is not positive.'),
            math(f'The sum of the first {n} terms of an arithmetic sequence is {n * (n + 2)}. Its first term is 3. What is its common difference?', 2, [1, 3, n + 2], 'Arithmetic sequences', f'Use S = n(2a + (n - 1)d)/2. Dividing by n gives {n + 2} = (6 + {n - 1}d)/2, so {n - 1}d = {2 * n - 2}, and d = 2.'),
            math(f'The equation x^2 + y^2 - {2 * n}x + 6y + {n * n - 16} = 0 describes a circle. What is its radius?', 5, [3, n + 6, 25], 'Circle equations', f'Completing both squares gives (x - {n})^2 + (y + 3)^2 = 25. The radius is the square root of 25, which is 5.'),
        ]
        # Ask for the larger solution so the item remains unique for every n.
        questions[0]['question_text'] = questions[0]['question_text'].replace('positive solution', 'larger solution')
        questions[0]['explanation'] = f'Composition gives (2x - {n})^2 + 1 = 26. Hence 2x - {n} = 5 or -5, so x = ({n} + 5)/2 or ({n} - 5)/2. The larger root is {n + 5}/2.'
    else:
        # Additional constraints and transformations distinguish the top tiers.
        power = level - 2
        questions = [
            math(f'The roots r and s of x^2 - {2 * n + 1}x + {n * (n + 1)} = 0 satisfy r < s. A function is defined by h(t) = (t - r) / (s - r). What is h(r^2 + s^2 - {2 * n * n})?', n + 1, [2 * n + 1, n, n * n + 1], 'Roots and transformed functions', f'The roots are r = {n} and s = {n + 1}, so s - r = 1. The input simplifies to {2 * n + 1}; subtracting r leaves {n + 1}.'),
            math(f'A box contains {n} red and {n + power} blue counters. Two are drawn without replacement. Given that at least one is red, what is the probability that both are red?', f'{n - 1}/{3 * n + 2 * power - 1}', [f'{n - 1}/{2 * n + power - 1}', '1/2', f'{n}/{2 * n + power}'], 'Conditional sample spaces', f'The favorable unordered pairs number n(n-1)/2 with n={n}. Pairs containing at least one red number n(n-1)/2 + n(n+{power}). Dividing and cancelling n/2 gives ({n - 1})/({3 * n + 2 * power - 1}).'),
            math(f'A right triangle has legs of length {3 * n} and {4 * n}. A circle is inscribed in the triangle, and a square is inscribed in that circle. What is the area of the square?', 2 * n * n, [n * n, 4 * n * n, 6 * n * n], 'Nested geometry', f'The hypotenuse is {5 * n}. The inradius is (a+b-c)/2 = {n}. The square diagonal is the circle diameter, {2 * n}; its area is diagonal squared divided by 2, or {2 * n * n}.'),
        ]
    reading = {
        'question_text': 'When the town announced plans to replace its wooden footbridge, historian Mara Lin asked volunteers to photograph it. She expected a record of its railings and supports. Instead, residents brought pictures of weddings, fishing trips, and walks to school. Lin initially set these aside because the bridge was often barely visible. Later, she arranged them beside the architectural photographs. Visitors lingered longest at the crowded family pictures, pointing out people and retelling stories. In her final exhibit notes, Lin described the bridge as both a structure people crossed and a place where their lives intersected. She retained the technical photographs, but gave the personal pictures equal space.\n\nWhich statement best describes the change in Lin\'s approach?',
        'options': ['She expanded a structural record to include the bridge\'s role in community life.', 'She abandoned historical documentation in favor of unrelated family portraits.', 'She concluded that technical photographs could not provide accurate information.', 'She decided that only photographs showing the entire bridge deserved display.'],
        'correct_option': 0, 'domain': 'reading_writing', 'section': 'Reading', 'skill': 'ACT Reading: Development of perspective',
        'explanation': 'Lin begins by seeking architectural details and setting aside personal images. She later displays both kinds equally and describes the bridge as a meeting place for lives. This expands her focus rather than abandoning documentation or rejecting technical photographs.',
    }
    english = {
        'question_text': 'The community garden began on an unused lot behind the library. Volunteers removed broken pavement and tested the soil before planting. The first summer brought a modest harvest, which they donated to a neighborhood kitchen. The following spring, the volunteers installed raised beds and a rain barrel. [The garden now supplies the kitchen with fresh produce throughout the growing season.] The library also hosts monthly workshops where new gardeners can learn from experienced volunteers.\n\nThe writer wants to emphasize how the garden\'s output has grown since its first summer. Which replacement for the bracketed sentence best accomplishes this goal?',
        'options': ['The garden now provides three times as much produce as it did during its first summer.', 'The garden is located on a lot behind the town library.', 'Several volunteers enjoy attending the monthly workshops.', 'Rain barrels can store water collected from nearby roofs.'],
        'correct_option': 0, 'domain': 'reading_writing', 'section': 'English', 'skill': 'ACT English: Writing purpose',
        'explanation': 'The first choice directly compares present production with the first summer and quantifies the increase. The other choices concern location, volunteers, or equipment; none explains growth in the garden\'s output.',
    }
    questions.extend([reading, english])
    for question in questions:
        answer = question['options'][question['correct_option']]
        rng.shuffle(question['options'])
        question.update(correct_option=question['options'].index(answer), difficulty=difficulty, source='fallback', exam='ACT')
    return questions
