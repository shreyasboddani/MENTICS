"""Digital-SAT-length Math benchmark: two 22-question modules.

Module 1 mixes easy, medium and a few hard items; Module 2 is weighted hard,
as the adaptive second module is for a strong student. Domain counts follow the
published blueprint (Algebra 15, Advanced Math 15, Problem Solving and Data
Analysis 7, Geometry and Trigonometry 7). Every answer is computed.
"""
import math
from fractions import Fraction

from bench_common import Retry, fac, money, num, pi_form, poly, register, spec, sub

SAT_MATH = []   # the 44 benchmark questions, in test order
SAT_EXTRA = []  # additional practice templates for recovery content


def sat(module, skill, difficulty, sub=None):
    return register(SAT_MATH, module, skill, difficulty, sub)


def extra(skill, difficulty, sub=None):
    return register(SAT_EXTRA, None, skill, difficulty, sub)


# ---------------------------------------------------------------- Module 1

@sat(1, 'linear_equations_one', 'easy', 'distribute and collect')
def _distribute(r):
    a, b = r.randint(3, 8), r.randint(2, 9)
    c = r.randint(1, a - 1)
    x0 = r.choice([v for v in range(-7, 10) if v])
    d = a * (x0 + b) - c * x0
    assert (a - c) * x0 == d - a * b
    rhs = poly({1: c, 0: d})
    return spec(f'What value of x satisfies the equation {a}(x + {b}) = {rhs}?', x0, [
        (Fraction(d - b, a - c), 'Distributed the multiplier to x but not to the constant.'),
        (Fraction(d + a * b, a - c), 'Moved the distributed constant with the wrong sign.'),
        (Fraction(d - a * b, a + c), 'Added the x-coefficients when collecting terms.')],
        f'Distribute {a} across the parentheses: {a}x + {a * b} = {rhs}. Subtract {poly({1: c})} and {a * b} from both sides to get {a - c}x = {num(d - a * b)}, so x = {num(x0)}. Substituting back makes both sides {num(a * (x0 + b))}.',
        ['Expand the left side before moving any terms.', 'Every term inside the parentheses gets multiplied by the outside factor.', 'Gather the x terms on one side and the constants on the other, then divide by the remaining coefficient.'])


@sat(1, 'percentages', 'easy', 'successive percent change')
def _discount_tax(r):
    P, p, t = r.choice([80, 120, 160, 200, 240, 320, 400]), r.choice([20, 25, 30, 40]), r.choice([5, 10, 20, 25])
    val = Fraction(P * (100 - p) * (100 + t), 10000)
    return spec(f'A jacket has a list price of ${P}. During a sale its price is reduced by {p}%. A sales tax of {t}% is then applied to the sale price. What is the total cost of the jacket, including tax?', money(val), [
        (money(Fraction(P * (100 - p + t), 100)), 'Combined the discount and tax into one net percent change.'),
        (money(Fraction(P * (100 - p - t), 100)), 'Treated the tax as a second discount.'),
        (money(Fraction(P * (100 - p), 100) + t), 'Added the tax rate as dollars.')],
        f'After a {p}% discount the price is {100 - p}% of ${P}, or {money(Fraction(P * (100 - p), 100))}. The tax applies to that sale price, so multiply by {Fraction(100 + t, 100)}: the total is {money(val)}. Percent changes applied one after another multiply; they do not add.',
        ['Apply the two changes in the order the problem describes.', 'A discount of p% leaves (100 − p)% of the price; tax multiplies by (100 + t)%.', 'Multiply the list price by both multipliers instead of adding the percents.'])


@sat(1, 'equivalent_expressions', 'easy', 'expand a product of binomials')
def _expand(r):
    p, a, b = r.randint(2, 5), r.randint(1, 7), r.randint(1, 7)
    mid = a - p * b
    if mid == 0:
        raise Retry
    right = poly({2: p, 1: mid, 0: -a * b})
    return spec(f'Which expression is equivalent to ({poly({1: p, 0: a})})(x − {b})?', right, [
        (poly({2: p, 1: a + p * b, 0: -a * b}), 'Made a sign error when combining the cross terms.'),
        (poly({2: p, 1: mid, 0: a * b}), 'Got the sign of the constant term wrong.'),
        (poly({2: p, 0: -a * b}), 'Multiplied only the first and last terms.')],
        f'Multiply each term: {p}x·x = {p}x², {p}x·(−{b}) = −{p * b}x, {a}·x = {a}x and {a}·(−{b}) = −{a * b}. Combining the x terms gives {num(mid)}x, so the product is {right}.',
        ['Use FOIL: first, outer, inner, last.', 'The two x terms come from the outer and inner products.', 'Combine the outer and inner products, keeping careful track of the negative sign.'])


@sat(1, 'lines_angles_triangles', 'easy', 'exterior angle theorem')
def _exterior(r):
    a, b, x0 = r.randint(2, 5), r.randint(2, 6), r.randint(6, 14)
    c = (a + b) * x0
    if c > 170 or a == b:
        raise Retry
    return spec(f'In triangle PQR, the measure of angle P is ({a}x)°, the measure of angle Q is ({b}x)°, and the measure of the exterior angle at R is {c}°. What is the measure of angle Q, in degrees?', b * x0, [
        (a * x0, 'Found angle P instead of angle Q.'),
        (180 - c, 'Reported the interior angle at R.'),
        (x0, 'Stopped after solving for x.')],
        f'An exterior angle equals the sum of the two remote interior angles: {a}x + {b}x = {c}, so x = {x0}. Angle Q measures {b} × {x0} = {b * x0}°.',
        ['Which two angles are remote from the exterior angle at R?', 'An exterior angle equals the sum of the two opposite interior angles.', 'Write an equation for that sum, solve for x, then substitute into the expression for angle Q.'])


@sat(1, 'linear_functions', 'easy', 'evaluate a linear model')
def _linear_model(r):
    m, k = r.choice([-6, -5, -4, -3, -2, 2, 3, 4, 5, 6]), r.randint(-9, 15)
    p = r.randint(1, 4)
    q, t = p + r.randint(2, 4), 0
    t = q + r.randint(3, 7)
    f = lambda x: m * x + k
    return spec(f'The function f is linear. f({p}) = {f(p)} and f({q}) = {f(q)}. What is f({t})?', f(t), [
        (f(q) - m * (t - q), 'Used the right rate of change with the wrong sign.'),
        (m * t, 'Dropped the y-intercept.'),
        (f(q) + (t - q), 'Used a rate of change of 1 instead of the computed slope.')],
        f'The slope is ({f(q)} − {num(f(p))}) / ({q} − {p}) = {m}. Moving from x = {q} to x = {t} changes the output by {m} × {t - q} = {m * (t - q)}, so f({t}) = {num(f(q))} + {num(m * (t - q))} = {num(f(t))}.',
        ['First find the constant rate of change between the two known points.', 'Output change = slope × input change.', 'Start from the nearer known point and add the change over the remaining distance.'])


@sat(1, 'systems_of_equations', 'medium', 'word problem system')
def _tickets(r):
    A, S, N, s = r.choice([14, 15, 16, 18]), r.choice([8, 9, 10]), r.randint(90, 160), r.randint(25, 70)
    M = A * (N - s) + S * s
    return spec(f'Tickets to a school concert cost ${A} for adults and ${S} for students. A total of {N} tickets were sold for ${M}. How many student tickets were sold?', s, [
        (N - s, 'Reported the number of adult tickets.'),
        (S * s, 'Reported the revenue from student tickets.'),
        (A * (N - s), 'Reported the revenue from adult tickets.')],
        f'Let s be student tickets, so adult tickets are {N} − s. Then {S}s + {A}({N} − s) = {M}. This gives {A * N} − {A - S}s = {M}, so s = {s}. Adult tickets number {N - s}, which is a different quantity.',
        ['Define one variable for students and express adults in terms of it.', 'Write one equation for the ticket count and one for the revenue.', 'Substitute the adult count into the revenue equation and solve for the variable you defined, then reread what is asked.'])


@sat(1, 'quadratic_functions', 'medium', 'maximum of a quadratic model')
def _max_height(r):
    a, t0, c = r.choice([4, 5, 8, 16]), r.randint(2, 5), r.randint(3, 40)
    b = 2 * a * t0
    top = c + a * t0 * t0
    return spec(f'The height, in feet, of a ball t seconds after it is thrown is given by h(t) = {poly({2: -a, 1: b, 0: c}, "t")}. What is the maximum height, in feet, that the ball reaches?', top, [
        (t0, 'Gave the time of the maximum, not the height.'),
        (c, 'Gave the starting height.'),
        (c + 2 * a * t0 * t0, 'Used b²/(2a) instead of b²/(4a).')],
        f'The parabola opens downward, so its vertex is the maximum. The vertex occurs at t = −b/(2a) = {t0}. Then h({t0}) = {-a}({t0})² + {b}({t0}) + {c} = {top}. The value {t0} is when the ball peaks, not how high it is.',
        ['The maximum of a downward-opening parabola is at its vertex.', 'The vertex has input t = −b/(2a).', 'Find that input first, then substitute it back into the function for the height.'])


@sat(1, 'ratios_rates', 'medium', 'change in a ratio')
def _ratio_change(r):
    a, b, dl, k = r.randint(2, 7), r.randint(2, 6), r.randint(1, 3), r.randint(4, 14)
    d, c = b + dl, k * dl
    return spec(f'At a community event the ratio of adults to children was {a} to {b}. After {c} more children arrived, the ratio of adults to children was {a} to {d}. How many adults were at the event?', a * k, [
        (b * k, 'Reported the original number of children.'),
        ((a + b) * k, 'Reported the original total attendance.'),
        (a * c, 'Multiplied the ratio term by the number of new children.')],
        f'Write the adults as {a}k and the original children as {b}k. After {c} more children, {a}k / ({b}k + {c}) = {a}/{d}, so {d}k = {b}k + {c} and k = {k}. The number of adults is {a} × {k} = {a * k}.',
        ['Represent the original numbers with a common multiplier.', 'The adults stay the same; only the children change, by exactly the number who arrived.', 'Set up the new ratio as an equation, solve for the multiplier, and then build the quantity requested.'])


@sat(1, 'linear_inequalities', 'easy', 'reverse the inequality sign')
def _flip(r):
    a, x0 = r.randint(2, 6), r.choice([v for v in range(-6, 9) if v])
    c = r.randint(-8, 12)
    b = c + a * x0
    return spec(f'Which inequality is equivalent to {poly({1: -a, 0: b})} ≥ {c}?', f'x ≤ {num(x0)}', [
        (f'x ≥ {num(x0)}', 'Forgot to reverse the inequality when dividing by a negative.'),
        (f'x ≤ {num(-x0)}', 'Made a sign error while isolating x.'),
        (f'x ≥ {num(-x0)}', 'Made a sign error and did not reverse the inequality.')],
        f'Subtract {b} from both sides: {-a}x ≥ {num(c - b)}. Dividing by {-a}, a negative number, reverses the inequality, giving x ≤ {num(x0)}. Testing x = {num(x0 - 1)} gives {num(-a * (x0 - 1) + b)} ≥ {c}, which is true.',
        ['Isolate the x term first.', 'Dividing or multiplying by a negative number changes the direction of the inequality.', 'After dividing, test a value on the side you chose to confirm the inequality still holds.'])


@sat(1, 'function_notation', 'medium', 'composite functions')
def _compose(r):
    a, b, m, c, k = r.randint(2, 9), r.randint(1, 4), r.randint(2, 5), r.randint(1, 9), r.randint(1, 4)
    f = lambda x: x * x - a
    g = lambda x: m * x + c
    return spec(f'The functions f and g are defined by f(x) = x² − {a} and g(x) = {m}x + {c}. What is the value of f(g({k}))?', f(g(k)), [
        (g(f(k)), 'Composed the functions in the wrong order.'),
        (f(k) * g(k), 'Multiplied the function values instead of composing them.'),
        (g(k) ** 2 - a * k, 'Substituted into the wrong position of the outer function.')],
        f'Work from the inside out. g({k}) = {m}({k}) + {c} = {g(k)}. Then f({g(k)}) = {g(k)}² − {a} = {f(g(k))}. The notation f(g(x)) means apply g first.',
        ['In f(g(k)), which function is applied first?', 'Evaluate the inner function at the given value.', 'Substitute that result into the outer function as its entire input.'])


@sat(1, 'area_volume', 'easy', 'perimeter to area')
def _rectangle(r):
    k, w = r.randint(2, 5), r.randint(3, 11)
    P = 2 * w * (k + 1)
    return spec(f'The length of a rectangle is {k} times its width. The perimeter of the rectangle is {P} centimeters. What is the area of the rectangle, in square centimeters?', k * w * w, [
        (4 * k * w * w, 'Treated the perimeter as the sum of length and width.'),
        (k * w, 'Multiplied length by the width ratio instead of by the width.'),
        ((k + 1) * w * w, 'Used the wrong side multiplier in the area.')],
        f'If the width is w, the length is {k}w and the perimeter is 2({k}w + w) = {2 * (k + 1)}w = {P}, so w = {w}. The length is {k * w} and the area is {k * w} × {w} = {k * w * w}.',
        ['Let the width be a variable and write the length in terms of it.', 'The perimeter counts both lengths and both widths.', 'Solve for the width, find the length, and only then compute the area.'])


@sat(1, 'nonlinear_equations', 'hard', 'extraneous solutions')
def _radical(r):
    b, s = r.randint(1, 5), r.randint(2, 5)
    r1, r2 = b + s, b + 1 - s
    a = b * b - r1 * r2
    left = f'√({poly({1: 1, 0: a})})'
    assert r1 + a == (r1 - b) ** 2 and r2 + a == (r2 - b) ** 2
    return spec(f'What is the solution to the equation {left} = x − {b}?', r1, [
        (r2, 'Kept an extraneous solution that makes the right side negative.'),
        (r1 + r2, 'Gave the sum of the roots of the squared equation.'),
        (s, 'Reported x − b instead of x.')],
        f'Square both sides: x + {a} = (x − {b})². Expanding gives x² − {2 * b + 1}x + {b * b - a} = 0, so x = {r1} or x = {r2}. The original equation requires x − {b} ≥ 0. Only {r1} works; {r2} makes the right side {r2 - b}, so it is extraneous.',
        ['Squaring both sides can introduce solutions that are not valid in the original equation.', 'After solving the squared equation, check each candidate in the original radical equation.', 'The square root cannot equal a negative number.'])


@sat(1, 'two_variable_data', 'medium', 'residuals')
def _residual(r):
    m, b, x = r.randint(3, 9), r.randint(10, 40), r.randint(3, 9)
    pred = m * x + b
    d = r.choice([d for d in range(3, 15) if d != m])
    actual = pred + r.choice([-1, 1]) * d
    way = 'above' if actual > pred else 'below'
    other = 'below' if way == 'above' else 'above'
    return spec(f'A line of best fit for the number of practice hours x and the score y on a skills test is y = {m}x + {b}. A student who practiced {x} hours scored {actual}. How far was the student’s score from the score predicted by the line, and in which direction?', f'{d} points {way} the prediction', [
        (f'{d} points {other} the prediction', 'Reversed the sign of the residual.'),
        (f'{pred} points {way} the prediction', 'Reported the predicted score, not the difference.'),
        (f'{actual} points {way} the prediction', 'Reported the actual score, not the difference.')],
        f'The prediction is {m}({x}) + {b} = {pred}. The student scored {actual}, which is {d} {way} {pred}. A positive residual means the point lies above the line.',
        ['Use the line to predict the score for this many hours.', 'The residual is the actual value minus the predicted value.', 'A positive difference means the actual score is above the prediction.'])


@sat(1, 'exponential_functions', 'medium', 'write an exponential model')
def _model_form(r):
    g, N0, d = r.choice([(2, 'doubles'), (3, 'triples'), (4, 'quadruples'), (5, 'quintuples')]), r.choice([120, 250, 400, 600]), r.choice([2, 3, 4, 6])
    n, verb = g
    return spec(f'A culture starts with {N0} bacteria. The number of bacteria {verb} every {d} hours. Which function models the number of bacteria, N, t hours after the culture starts?', f'N(t) = {N0}({n})^(t/{d})', [
        (f'N(t) = {N0}({n})^({d}t)', 'Multiplied the exponent by the period instead of dividing.'),
        (f'N(t) = {N0}({n - 1})^(t/{d})', 'Used the growth amount instead of the growth factor.'),
        (f'N(t) = ({N0}/{d})({n})^t', 'Applied the growth factor every hour.')],
        f'Growth by a factor of {n} occurs once per {d} hours. After t hours there have been t/{d} such periods, so N(t) = {N0}({n})^(t/{d}). At t = {d} it equals {N0 * n}, which is {n} times the start.',
        ['How many growth periods occur in t hours?', 'Each period multiplies the amount by the same factor.', 'Put the number of periods in the exponent and test t equal to one period.'])


@sat(1, 'circles', 'medium', 'arc length')
def _arc(r):
    th, rad = r.choice([40, 45, 60, 72, 90, 120, 150, 200, 240]), r.randint(3, 15)
    L = Fraction(rad * th, 180)
    area = Fraction(rad * rad * th, 360)
    return spec(f'A circle has a radius of {rad} centimeters. What is the length, in centimeters, of an arc intercepted by a central angle of {th}°?', pi_form(L), [
        (pi_form(area), 'Gave the sector area instead of the arc length.'),
        (pi_form(Fraction(rad * th, 360)), 'Used πr instead of 2πr for the circumference.'),
        (pi_form(2 * rad), 'Gave the full circumference.')],
        f'An arc is the fraction {th}/360 of the circumference. The circumference is 2π({rad}) = {2 * rad}π, so the arc length is ({th}/360)({2 * rad}π) = {pi_form(L)} centimeters.',
        ['The arc is a fraction of the full circumference.', 'The fraction is the central angle divided by 360°.', 'Find the circumference first, then take that fraction of it.'])


@sat(1, 'linear_equations_two', 'medium', 'parallel lines and intercepts')
def _parallel(r):
    m, k, p, q = r.choice([2, 3, 4, 5, -2, -3, -4]), r.randint(-6, 8), r.randint(1, 6), r.randint(-9, 12)
    c = q - m * p
    if c == k:
        raise Retry
    return spec(f'Line ℓ has the equation y = {poly({1: m, 0: k})}. Line n is parallel to line ℓ and passes through the point ({p}, {q}). What is the y-intercept of line n?', c, [
        (q, 'Used the y-coordinate of the point as the intercept.'),
        (q + m * p, 'Made a sign error when moving from the point to x = 0.'),
        (k, 'Kept the intercept of line ℓ.')],
        f'Parallel lines share a slope, so line n has slope {m}. Using y = {m}x + b at ({p}, {q}): {q} = {m * p} + b, so b = {c}.',
        ['What must be true about the slopes of parallel lines?', 'Write y = mx + b for the new line using that slope.', 'Substitute the given point and solve for b.'])


@sat(1, 'probability', 'medium', 'conditional probability from a table')
def _conditional(r):
    sp10, sp11, fr10, fr11 = r.randint(18, 40), r.randint(15, 38), r.randint(12, 30), r.randint(14, 34)
    total = sp10 + sp11 + fr10 + fr11
    table = f'| | Grade 10 | Grade 11 |\n|---|---|---|\n| Spanish | {sp10} | {sp11} |\n| French | {fr10} | {fr11} |'
    return spec('A student who takes French is chosen at random from the students in the table. What is the probability that the student is in Grade 11?', Fraction(fr11, fr10 + fr11), [
        (Fraction(fr11, total), 'Divided by the total number of students instead of French students.'),
        (Fraction(fr11, sp11 + fr11), 'Reversed the condition: French among Grade 11 students.'),
        (Fraction(fr10, fr10 + fr11), 'Used the Grade 10 French count.')],
        f'The sample space is the French students only: {fr10} + {fr11} = {fr10 + fr11}. Of those, {fr11} are in Grade 11, so the probability is {num(Fraction(fr11, fr10 + fr11))}. Conditional probability restricts the denominator to the given group.',
        ['Which group does the problem tell you the student comes from?', 'That group, not the whole table, is the denominator.', 'Count the Grade 11 students inside that group for the numerator.'],
        source=f'Students in a school by language and grade:\n\n{table}')


@sat(1, 'desmos_strategy', 'hard', 'graph to find intersections')
def _intersections(r):
    r1, r2 = r.sample(range(-6, 8), 2)
    if abs(r1 - r2) < 2:
        raise Retry
    s, t = r.randint(-3, 4), r.randint(-6, 6)
    p, q = s - (r1 + r2), t + r1 * r2
    return spec(f'The graphs of y = {poly({2: 1, 1: p, 0: q})} and y = {poly({1: s, 0: t})} in the xy-plane intersect at two points. What is the positive difference of the x-coordinates of the two points?', abs(r1 - r2), [
        (abs(r1 + r2), 'Gave the magnitude of the sum of the x-coordinates.'),
        (abs(r1 * r2), 'Gave the magnitude of the product of the x-coordinates.'),
        (abs(r1 - r2) + 1, 'Miscounted the distance between the two coordinates.')],
        f'Setting the expressions equal gives x² + {num(p - s)}x + {num(q - t)} = 0, which factors as ({sub('x', r1)})({sub('x', r2)}) = 0. The x-coordinates are {num(r1)} and {num(r2)}, which differ by {abs(r1 - r2)}. In Desmos you can graph both equations and tap the two intersection points to read their coordinates.',
        ['Graph both equations in Desmos and tap each intersection point.', 'Or set the two expressions equal and move everything to one side.', 'Find both x-coordinates, then subtract the smaller from the larger.'])


@sat(1, 'linear_equations_one', 'medium', 'no-solution condition')
def _no_solution(r):
    a, k0, b = r.randint(2, 6), r.randint(2, 7), r.randint(3, 9)
    c = a * k0
    d = a * b + r.choice([-4, -3, -2, 2, 3, 5])
    return spec(f'In the equation {a}(kx + {b}) = {c}x + {d}, k is a constant. If the equation has no solution, what is the value of k?', k0, [
        (c, 'Set k equal to the coefficient on the right without dividing by the multiplier.'),
        (a * c, 'Multiplied instead of dividing.'),
        (b, 'Used the constant inside the parentheses.')],
        f'Distribute to get {a}kx + {a * b} = {c}x + {d}. For the equation to have no solution the x terms must cancel while the constants disagree: {a}k = {c}, so k = {k0}. The constants {a * b} and {d} are unequal, so the statement is false for every x.',
        ['A linear equation has no solution when both sides have the same slope but different constants.', 'Distribute first so both sides have the form (coefficient)x + constant.', 'Set the x coefficients equal and confirm the constants are different.'])


@sat(1, 'equivalent_expressions', 'medium', 'factor a quadratic')
def _factor(r):
    a, p, q = r.choice([2, 3, 4]), r.choice([-7, -5, -3, -1, 1, 3, 5, 7]), r.choice([-6, -4, -2, 2, 3, 4, 6])
    mid = a * q + p
    if mid == 0:
        raise Retry
    target = poly({2: a, 1: mid, 0: p * q})
    return spec(f'Which expression is equivalent to {target}?', f'{fac(a, p)}{fac(1, q)}', [
        (f'{fac(a, -p)}{fac(1, -q)}', 'Flipped both signs in the factors.'),
        (f'{fac(a, q)}{fac(1, p)}', 'Swapped the constants between the factors.'),
        (f'{fac(a, p)}{fac(1, -q)}', 'Flipped one sign in the factors.')],
        f'Expanding {fac(a, p)}{fac(1, q)} gives {target}: the outer and inner products are {num(a * q)}x and {num(p)}x, which combine to {num(mid)}x, and the constants multiply to {num(p * q)}. Check a candidate by multiplying it out.',
        ['Identify two numbers that multiply to give the constant term.', 'The middle coefficient comes from the outer and inner products.', 'Test each answer choice by expanding it; only one reproduces every term.'])


@sat(1, 'right_triangles_trig', 'medium', 'tangent and scaling')
def _tangent(r):
    a, b, h = r.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29)])
    k = r.randint(2, 4)
    return spec(f'In right triangle ABC, angle C is the right angle, tan A = {a}/{b}, and AB = {k * h}. What is the length of BC?', k * a, [
        (k * b, 'Mixed up the opposite and adjacent sides.'),
        (k * (a + b), 'Added the legs.'),
        (Fraction(k * h * a, b), 'Multiplied the hypotenuse by the tangent.')],
        f'In the right triangle with legs {a} and {b}, the hypotenuse is {h}. The triangle is scaled by {k}, because AB = {k * h}. Side BC is opposite angle A, so BC = {k} × {a} = {k * a}.',
        ['Sketch the triangle and mark which side is opposite angle A.', 'A tangent ratio gives the legs; find the hypotenuse of that ratio triangle.', 'Compare the given hypotenuse to the ratio triangle’s hypotenuse to find the scale factor.'])


@sat(1, 'nonlinear_equations', 'easy', 'absolute value equations')
def _absolute(r):
    p, m, s = r.choice([2, 3, 4, 5]), r.randint(2, 6), r.randint(2, 9)
    q = p * m
    x1, x2 = Fraction(q + s, p), Fraction(q - s, p)
    if x1.denominator != 1 or x2.denominator != 1 or x2 == x1:
        raise Retry
    return spec(f'What is the sum of the solutions of the equation |{p}x − {q}| = {s}?', 2 * m, [
        (x1, 'Reported only the larger solution.'),
        (m, 'Reported the midpoint, half the sum.'),
        (x1 * x2, 'Reported the product of the solutions.')],
        f'Absolute value gives two equations: {p}x − {q} = {s} and {p}x − {q} = −{s}. They give x = {num(x1)} and x = {num(x2)}. Their sum is {num(x1 + x2)}.',
        ['An absolute value equation usually has two cases.', 'Set the inside equal to the value and to its opposite.', 'Solve each case, then add the two solutions.'])


# ---------------------------------------------------------------- Module 2

@sat(2, 'linear_equations_two', 'hard', 'perpendicular lines')
def _perpendicular(r):
    a, b, t, q = r.randint(2, 5), r.randint(2, 5), r.randint(1, 4), r.randint(-8, 10)
    if a == b:
        raise Retry
    c, p = a * b * r.randint(1, 3), a * t
    return spec(f'Line ℓ has the equation {a}x + {b}y = {c}. Line m is perpendicular to line ℓ and passes through the point ({p}, {q}). At what y-coordinate does line m cross the y-axis?', q - b * t, [
        (q + b * t, 'Made a sign error moving from the point to the y-axis.'),
        (q + Fraction(a * p, b), 'Used the slope of ℓ, giving a parallel line.'),
        (q - Fraction(a * p, b), 'Used the positive slope a/b for the perpendicular.')],
        f'Line ℓ has slope −{a}/{b}, so a perpendicular line has slope {b}/{a}. From ({p}, {q}) go back {p} units in x to reach the y-axis, changing y by {b}/{a} × {p} = {b * t}. The intercept is {q} − {b * t} = {q - b * t}.',
        ['Rewrite line ℓ in slope-intercept form to read its slope.', 'Perpendicular slopes are negative reciprocals.', 'Use the new slope and the given point to find b in y = mx + b.'])


@sat(2, 'systems_of_equations', 'hard', 'no solution to a system')
def _system_no_solution(r):
    a, b, lam, c = r.randint(2, 6), r.randint(2, 6), r.randint(2, 4), r.randint(3, 15)
    e = lam * c + r.choice([-5, -3, 3, 5, 7])
    return spec('In the system of equations above, k is a constant. If the system has no solution, what is the value of k?', lam * a, [
        (a + lam, 'Added the multiplier instead of multiplying.'),
        (lam * b, 'Matched the y coefficient instead of the x coefficient.'),
        (a, 'Assumed k must equal the first equation’s x coefficient.')],
        f'The y coefficient of the second equation is {lam} times that of the first, so the x coefficient must also be {lam} times as large: k = {lam} × {a} = {lam * a}. The constants do not follow the same pattern ({lam} × {c} = {lam * c}, not {e}), so the lines are parallel and distinct.',
        ['A system with no solution represents two parallel lines.', 'Parallel lines have proportional x and y coefficients but a different constant.', 'Find the multiplier that takes the first y coefficient to the second, and apply it to the x coefficient.'],
        source=f'{a}x + {b}y = {c}\nkx + {lam * b}y = {e}')


@sat(2, 'linear_inequalities', 'hard', 'optimize under a budget')
def _van_budget(r):
    S, gap, N, l0 = r.choice([80, 90, 100]), r.randint(40, 80), r.randint(6, 12), r.randint(2, 5)
    L = S + gap
    B = S * N + gap * l0 + r.randint(1, gap - 1)
    return spec(f'A school trip needs exactly {N} vans. A large van rents for ${L} and a small van rents for ${S}. The budget for van rentals is ${B}. What is the greatest number of large vans the school can rent?', l0, [
        (l0 + 1, 'Rounded up even though the budget cannot be exceeded.'),
        (B // L, 'Ignored the small vans that must also be rented.'),
        (N - l0, 'Reported the number of small vans.')],
        f'If l vans are large, then {N} − l are small. The cost is {L}l + {S}({N} − l) ≤ {B}, which simplifies to {S * N} + {gap}l ≤ {B}. So l ≤ {num(Fraction(B - S * N, gap))}. Since l is a whole number and the budget cannot be exceeded, l = {l0}.',
        ['Let one variable be the number of large vans and write the small vans in terms of it.', 'Translate “budget” as a less-than-or-equal-to inequality on total cost.', 'Solve the inequality, then round in the direction that stays within the budget.'])


@sat(2, 'linear_functions', 'medium', 'rate and starting amount')
def _tank(r):
    rate, T, t1 = r.randint(3, 9), r.randint(15, 30), r.randint(2, 5)
    t2 = t1 + r.randint(3, 8)
    V0 = rate * T
    return spec(f'Water drains from a tank at a constant rate. After {t1} minutes the tank holds {V0 - rate * t1} gallons, and after {t2} minutes it holds {V0 - rate * t2} gallons. How many minutes after the draining began will the tank be empty?', T, [
        (T - t2, 'Found the time remaining after the second measurement.'),
        (T - t1, 'Found the time remaining after the first measurement.'),
        (V0, 'Reported the starting volume.')],
        f'The volume falls by {rate * (t2 - t1)} gallons in {t2 - t1} minutes, a rate of {rate} gallons per minute. So the tank started with {V0 - rate * t1} + {rate} × {t1} = {V0} gallons and is empty after {V0}/{rate} = {T} minutes from the start.',
        ['Find the constant rate of change from the two measurements.', 'Use that rate to work back to the starting volume.', 'Divide the starting volume by the rate to find when the volume reaches zero.'])


@sat(2, 'linear_equations_one', 'hard', 'equation with fractions')
def _fractions(r):
    b, d = r.choice([(2, 3), (3, 4), (2, 5), (3, 5), (4, 5)])
    a, c, x0 = r.randint(1, 5), r.randint(1, 5), r.randint(3, 20)
    e = Fraction(x0 + a, b) - Fraction(x0 - c, d)
    bd = b * d
    expr = f'(x + {a})/{b} − (x − {c})/{d} = {num(e)}'
    return spec(f'What value of x satisfies the equation {expr}?', x0, [
        (Fraction(e * bd - a * d + b * c, d - b), 'Made a sign error when distributing the negative.'),
        (Fraction(e * bd - a * d - b * c, d + b), 'Added the x coefficients instead of subtracting.'),
        (-x0, 'Reversed the sign of the final answer.')],
        f'Multiply every term by {bd}: {d}(x + {a}) − {b}(x − {c}) = {num(e * bd)}. Distributing gives {d - b}x + {a * d + b * c} = {num(e * bd)}, so x = {x0}. Take care with the minus sign in front of the second fraction.',
        ['Clear the fractions by multiplying both sides by a common denominator.', 'A minus sign in front of a fraction applies to the whole numerator.', 'After clearing fractions, combine like terms and solve the linear equation.'])


@sat(2, 'systems_of_equations', 'medium', 'combine equations')
def _x_plus_y(r):
    p, q = r.sample(range(2, 9), 2)
    x0, y0 = r.sample(range(1, 10), 2)
    A, B = p * x0 + q * y0, q * x0 + p * y0
    return spec('The solution to the system of equations above is (x, y). What is the value of x + y?', x0 + y0, [
        (x0, 'Reported x only.'),
        (y0, 'Reported y only.'),
        (A + B, 'Reported the sum of the right-hand sides.')],
        f'Add the equations: {p + q}x + {p + q}y = {A + B}. Dividing by {p + q} gives x + y = {x0 + y0} without solving for either variable separately.',
        ['Look at the coefficients before solving for x and y individually.', 'What happens if you add the two equations?', 'Factor the common coefficient out of the sum and divide.'],
        source=f'{p}x + {q}y = {A}\n{q}x + {p}y = {B}')


@sat(2, 'desmos_strategy', 'hard', 'tangent lines and parameters')
def _tangent_line(r):
    b, c, u = r.randint(-4, 4), r.randint(-5, 6), r.randint(1, 4)
    m = b - 2 * u
    k = c - u * u
    if m == 0:
        raise Retry
    return spec(f'For what value of k does the line y = {poly({1: m})} + k intersect the parabola y = {poly({2: 1, 1: b, 0: c})} at exactly one point?', k, [
        (c + u * u, 'Made a sign error in the discriminant condition.'),
        (c, 'Used the parabola’s y-intercept.'),
        (c - 2 * u, 'Used half of the coefficient difference instead of its square.')],
        f'Setting the equations equal gives x² + {num(b - m)}x + {num(c)} − k = 0. One intersection means the discriminant is zero: {num(b - m)}² − 4({c} − k) = 0, so k = {c} − {u * u} = {k}. In Desmos, add a slider for k and watch for the value where the line just touches the parabola.',
        ['Exactly one intersection means the line is tangent to the parabola.', 'Set the two expressions equal and look at the discriminant of the resulting quadratic.', 'Set the discriminant equal to zero and solve for k, or graph with a slider for k.'])


@sat(2, 'linear_equations_two', 'medium', 'intercepts and area')
def _intercept_triangle(r):
    a, b, t = r.randint(2, 6), r.randint(2, 6), r.randint(1, 3)
    if a == b:
        raise Retry
    c = a * b * t
    return spec(f'The graph of {a}x + {b}y = {c} in the xy-plane forms a triangle with the x-axis and the y-axis. What is the area of the triangle?', Fraction(a * b * t * t, 2), [
        (a * b * t * t, 'Forgot the factor of one-half.'),
        (b * t + a * t, 'Added the intercepts.'),
        (Fraction(c * c, 2), 'Used the constant c for both legs.')],
        f'The x-intercept is {c}/{a} = {b * t} and the y-intercept is {c}/{b} = {a * t}. These are the legs of a right triangle, so the area is (1/2)({b * t})({a * t}) = {num(Fraction(a * b * t * t, 2))}.',
        ['Find where the line crosses each axis by setting the other variable to zero.', 'The intercepts are the two legs of a right triangle.', 'Area of a triangle is one-half base times height.'])


@sat(2, 'quadratic_functions', 'hard', 'range of a quadratic')
def _no_real_solutions(r):
    a, h, c = r.randint(2, 5), r.randint(1, 5), r.randint(-9, 9)
    top = c + a * h * h
    return spec(f'The function f is defined by f(x) = {poly({2: -a, 1: 2 * a * h, 0: c})}. For which values of n does the equation f(x) = n have no real solutions?', f'n > {top}', [
        (f'n < {top}', 'Reversed which side of the maximum has no solutions.'),
        (f'n > {c}', 'Compared to the y-intercept instead of the maximum.'),
        (f'n > {h}', 'Used the x-coordinate of the vertex.')],
        f'The parabola opens downward, so its maximum value is at the vertex. The vertex is at x = {h}, and f({h}) = {top}. The equation f(x) = n has a real solution only when n ≤ {top}, so there is none when n > {top}.',
        ['Think of f(x) = n as a horizontal line meeting the graph.', 'Does this parabola open up or down, and what does that say about its range?', 'Find the vertex value; horizontal lines beyond it never touch the graph.'])


@sat(2, 'nonlinear_equations', 'hard', 'line and parabola intersect')
def _system_sum(r):
    r1, r2 = r.sample(range(-5, 7), 2)
    m, n = r.randint(-3, 4), r.randint(-6, 6)
    b, c = m - (r1 + r2), n + r1 * r2
    total = m * (r1 + r2) + 2 * n
    return spec(f'A line and a parabola are graphed in the xy-plane: y = {poly({2: 1, 1: b, 0: c})} and y = {poly({1: m, 0: n})}. They intersect at two points. What is the sum of the y-coordinates of the two points?', total, [
        (r1 + r2, 'Gave the sum of the x-coordinates.'),
        (m * (r1 + r2), 'Forgot the constant term of the line for each point.'),
        (c + n, 'Added the constants of the two equations.')],
        f'Setting the expressions equal: x² + {num(b - m)}x + {num(c - n)} = 0, so the x-coordinates are {num(r1)} and {num(r2)}. On the line, y = {poly({1: m, 0: n})}: the y-coordinates are {num(m * r1 + n)} and {num(m * r2 + n)}, which sum to {num(total)}.',
        ['Find the x-coordinates of the intersection points first.', 'Substitute each x into the simpler equation, the line.', 'Compute both y-values and add them.'])


@sat(2, 'exponential_functions', 'hard', 'half-life and units')
def _half_life(r):
    u, n = r.choice([2, 3]), r.choice([3, 4])
    h, W = 7 * u, n * u
    j = r.choice([6, 12, 18, 24])
    M0 = j * 2 ** n
    return spec(f'A sample of a radioactive substance has a mass of {M0} grams. Its half-life is {h} days. What is the mass of the sample, in grams, after {W} weeks?', j, [
        (Fraction(M0, 2 * n), 'Treated each half-life as dividing by 2 a total of n times as a linear change.'),
        (Fraction(M0, 2 ** (n - 1)), 'Used one fewer half-life than elapsed.'),
        (Fraction(M0, 2 ** (n + 1)), 'Used one more half-life than elapsed.')],
        f'{W} weeks is {7 * W} days. That is {7 * W}/{h} = {n} half-lives. The mass halves {n} times: {M0}/2^{n} = {j} grams.',
        ['Put the elapsed time and the half-life in the same unit.', 'How many half-lives fit into the elapsed time?', 'Halve the mass once per half-life, which means dividing by 2 raised to the number of half-lives.'])


@sat(2, 'function_notation', 'hard', 'transform a vertex')
def _transform(r):
    h, k, a, s, t = r.randint(-4, 5), r.randint(-5, 6), r.randint(2, 4), r.randint(1, 5), r.randint(1, 6)
    return spec(f'The graph of y = f(x) in the xy-plane has a vertex at ({num(h)}, {num(k)}). The function g is defined by g(x) = −{a}f(x + {s}) + {t}. What are the coordinates of the vertex of the graph of y = g(x)?', f'({num(h - s)}, {num(-a * k + t)})', [
        (f'({num(h + s)}, {num(-a * k + t)})', 'Shifted horizontally in the wrong direction.'),
        (f'({num(h - s)}, {num(-a * k - t)})', 'Subtracted the vertical shift.'),
        (f'({num(h - s)}, {num(-a * (k + t))})', 'Applied the stretch to the vertical shift as well.')],
        f'Replacing x with x + {s} moves the graph {s} units left, so the x-coordinate becomes {num(h - s)}. Multiplying by −{a} reflects and stretches, turning the y-value {num(k)} into {num(-a * k)}, and adding {t} shifts it up to {num(-a * k + t)}.',
        ['Track the vertex through each transformation in the order the function applies it to x and then to the output.', 'Inside changes affect x in the opposite direction; outside changes affect y directly.', 'Apply the horizontal shift to x, then the reflection and stretch to y, then the vertical shift.'])


@sat(2, 'equivalent_expressions', 'hard', 'polynomial division')
def _quotient(r):
    a, d, e, R = r.randint(2, 4), r.randint(1, 5), r.choice([-5, -3, -2, 2, 3, 4]), r.choice([2, 3, 4, 5, 7])
    b, c = e + a * d, d * e + R
    num_poly = poly({2: a, 1: b, 0: c})
    return spec(f'Which expression is equivalent to ({num_poly})/(x + {d}), where x ≠ −{d}?', f'{poly({1: a, 0: e})} + {R}/(x + {d})', [
        (f'{poly({1: a, 0: b})} + {R}/(x + {d})', 'Kept the original middle coefficient instead of carrying the division through.'),
        (f'{poly({1: a, 0: e})} − {R}/(x + {d})', 'Subtracted the remainder.'),
        (f'{poly({1: a, 0: e})} + {c}/(x + {d})', 'Used the original constant as the remainder.')],
        f'Divide: {a}x² + {num(b)}x + {num(c)} = (x + {d})({poly({1: a, 0: e})}) + {R}, because (x + {d})({poly({1: a, 0: e})}) = {poly({2: a, 1: b, 0: d * e})}. So the quotient is {poly({1: a, 0: e})} with remainder {R}.',
        ['Try polynomial long division or synthetic division by x + d.', 'Multiply the quotient back by the divisor to check it accounts for most of the numerator.', 'Whatever is left over after multiplying is the remainder over the divisor.'])


@sat(2, 'quadratic_functions', 'medium', 'sum of squares of roots')
def _root_squares(r):
    r1, r2 = r.sample(range(-7, 9), 2)
    s, p = r1 + r2, r1 * r2
    if s == 0 or p == 0:
        raise Retry
    return spec(f'What is the sum of the squares of the solutions to the equation {poly({2: 1, 1: -s, 0: p})} = 0?', r1 * r1 + r2 * r2, [
        (s * s, 'Squared the sum of the solutions and forgot to subtract 2p.'),
        (s * s + 2 * p, 'Used the wrong sign when removing the cross term.'),
        (s * s - p, 'Subtracted p instead of 2p.')],
        f'The solutions are {num(r1)} and {num(r2)}, since ({sub('x', r1)})({sub('x', r2)}) expands to the given quadratic. Their squares are {r1 * r1} and {r2 * r2}, which sum to {r1 * r1 + r2 * r2}. Equivalently, r₁² + r₂² = (r₁ + r₂)² − 2r₁r₂ = {s * s} − {2 * p}.',
        ['Factor the quadratic to find its two solutions.', 'Square each solution separately.', 'Add the two squares; do not square the sum.'])


@sat(2, 'nonlinear_equations', 'hard', 'rational equations and excluded values')
def _rational(r):
    a = r.randint(2, 6)
    if r.random() < .5:
        eq = f'1/(x − {a}) + 1/(x + {a}) = {2 * a}/(x² − {a * a})'
        return spec(f'Which of the following is the solution set of the equation {eq}?', 'There are no solutions.', [
            (f'x = {a}', 'Did not check the excluded value.'),
            (f'x = {num(-a)}', 'Used the wrong excluded value.'),
            (f'x = {a} and x = {num(-a)}', 'Took the factors of the denominator as solutions.')],
            f'Combine the left side over x² − {a * a}: 2x/(x² − {a * a}) = {2 * a}/(x² − {a * a}), so 2x = {2 * a} and x = {a}. But x = {a} makes the denominators zero, so it is excluded. The equation has no solution.',
            ['Find a common denominator and combine the fractions.', 'Solve the resulting simple equation.', 'Always check every solution against the values that make a denominator zero.'])
    b = r.choice([v for v in range(1, 9) if v != a])
    eq = f'1/(x − {a}) + 1/(x + {a}) = {2 * b}/(x² − {a * a})'
    return spec(f'Which of the following is the solution set of the equation {eq}?', f'x = {b}', [
        ('There are no solutions.', 'Assumed an excluded value was used when it was not.'),
        (f'x = {a}', 'Reported an excluded value.'),
        (f'x = {2 * b}', 'Forgot to divide by 2.')],
        f'Combine the left side: 2x/(x² − {a * a}) = {2 * b}/(x² − {a * a}), so 2x = {2 * b} and x = {b}. This is not {a} or −{a}, so it is allowed.',
        ['Find a common denominator and combine the fractions.', 'Set the numerators equal and solve.', 'Check the solution against the values that make a denominator zero.'])


@sat(2, 'exponential_functions', 'medium', 'equivalent rates')
def _hourly_rate(r):
    d = r.choice([2, 3, 4, 5])
    thing, unit = r.choice([('bacteria in a culture', 'hour'), ('users of an app', 'month'), ('views of a video', 'day')])
    right = round((2 ** (1 / d) - 1) * 100)
    return spec(f'The number of {thing} doubles every {d} {unit}s. Which of the following is closest to the percent increase each {unit}?', f'{right}%', [
        (f'{round(100 / d)}%', 'Divided 100% by the doubling period.'),
        (f'{round(2 ** (1 / d) * 100)}%', 'Reported the growth factor as a percent increase.'),
        (f'{round(math.log(2) / d * 100)}%', 'Used a continuous rate instead of a per-period percent increase.')],
        f'Each {unit} multiplies the amount by b where b^{d} = 2, so b = 2^(1/{d}) ≈ {2 ** (1 / d):.3f}. That is a {right}% increase per {unit}. Dividing 100% by {d} ignores compounding.',
        ['Growth factors multiply; percent changes do not simply divide.', 'Find the per-unit factor b so that b raised to the doubling period equals 2.', 'Convert the factor to a percent increase by subtracting 1.'])


@sat(2, 'one_variable_data', 'hard', 'effects on mean, median and range')
def _data_effects(r):
    n = r.choice([7, 9, 11])
    data = sorted(r.sample(range(3, 60), n))
    k = r.randint(6, 25)
    shown = ', '.join(str(v) for v in data)
    return spec(f'A data set has {n} values: {shown}. The two greatest values are each increased by {k}. Which of the following must be true about the new data set compared with the original?', 'The median is unchanged, and the mean and the range increase.', [
        ('The median and the mean both increase.', 'Assumed the median changes when extreme values change.'),
        ('The mean is unchanged, and the range increases.', 'Assumed the mean ignores the change in the largest values.'),
        ('The median and the range are both unchanged.', 'Forgot that the range depends on the greatest value.')],
        f'Increasing the two greatest values raises the total, so the mean increases. The middle value, the {(n + 1) // 2}th, is not one of the two greatest, so the median stays {data[n // 2]}. The greatest value rises by {k}, so the range increases.',
        ['Which values change and which stay put?', 'The mean depends on every value; the median depends only on the middle position.', 'The range is the greatest minus the least, so check whether either end moved.'])


@sat(2, 'sample_inference', 'hard', 'combining two margins of error')
def _two_polls(r):
    base = r.randint(40, 60)
    pa, ma, pb, mb = base + r.randint(1, 4), r.randint(2, 4), base - r.randint(0, 3), r.randint(3, 5)
    lo, hi = max(pa - ma, pb - mb), min(pa + ma, pb + mb)
    if hi - lo < 2:
        raise Retry
    inside = r.randint(lo + 1, hi - 1) if hi - lo > 2 else lo + 1
    only_a = pa + ma if pa + ma > hi else pa - ma
    only_b = pb - mb if pb - mb < lo else pb + mb
    outside = lo - 3
    if lo <= only_a <= hi or lo <= only_b <= hi or only_a == only_b:
        raise Retry
    opts = [(f'{only_a}%', 'Only consistent with one of the two polls.'),
            (f'{only_b}%', 'Only consistent with the other poll.'),
            (f'{outside}%', 'Not consistent with either poll.')]
    return spec(f'Two independent random polls estimated the percentage of voters in a city who support a transit plan. Poll A found {pa}% with a margin of error of {ma} percentage points. Poll B found {pb}% with a margin of error of {mb} percentage points. Which of the following is a plausible value of the actual percentage of voters in the city who support the plan, given both polls?', f'{inside}%', opts,
        f'Poll A supports values from {pa - ma}% to {pa + ma}%, and Poll B supports values from {pb - mb}% to {pb + mb}%. A value consistent with both must be in both intervals: {lo}% to {hi}%. Only {inside}% falls in both.',
        ['Compute the interval each poll supports.', 'The true value must be plausible for both polls at once.', 'Find the overlap of the two intervals and choose a value inside it.'])


@sat(2, 'statistical_claims', 'hard', 'random assignment and random selection')
def _volunteers(r):
    n, group, treat = r.choice([120, 180, 240, 300]), r.choice(['adult volunteers', 'high school volunteers', 'volunteer runners', 'volunteer employees']), r.choice(['a new sleep schedule', 'a daily mindfulness exercise', 'a revised study routine', 'a new warm-up routine'])
    return spec(f'Researchers recruited {n} {group} to test {treat}. They randomly assigned half of the participants to use it and half not to, and the group that used it showed a significantly better outcome. Which conclusion is best supported by the study design?', f'{treat.capitalize()} caused the improvement among participants like these volunteers, but the results may not generalize to everyone.', [
        (f'{treat.capitalize()} would improve the outcome for the entire population, because the participants were randomly assigned.', 'Confused random assignment with random selection.'),
        (f'{treat.capitalize()} is associated with the improvement, but the design cannot show cause.', 'Treated an experiment like an observational study.'),
        ('The improvement was likely due to the participants volunteering, so no conclusion can be drawn.', 'Dismissed random assignment because the group volunteered.')],
        'Random assignment supports a causal conclusion for the people in the study because it balances other factors between groups. The participants were volunteers, not a random sample of a larger population, so the result cannot safely be extended to everyone.',
        ['Separate two questions: how were participants chosen, and how were they assigned to groups?', 'Random assignment supports cause-and-effect; random selection supports generalizing.', 'Decide which of the two the study used and match each claim to it.'])


@sat(2, 'right_triangles_trig', 'hard', 'complementary angles')
def _cofunction(r):
    p, rr, x0, q = r.randint(2, 5), r.randint(1, 4), r.randint(3, 9), r.randint(2, 12)
    s = 90 - q - (p + rr) * x0
    if s <= 4 or p * x0 + q >= 88 or rr * x0 + s >= 88:
        raise Retry
    return spec(f'In a right triangle, angles A and B are the acute angles. sin({p}x + {q})° = cos({rr}x + {s})°, where {p}x + {q} is the measure of angle A and {rr}x + {s} is the measure of angle B. What is the value of x?', x0, [
        (Fraction(s - q, p - rr) if p != rr else x0 + 1, 'Set the two angle measures equal.'),
        (Fraction(180 - q - s, p + rr), 'Used 180° instead of 90° for the two acute angles.'),
        (Fraction(90 - q, p), 'Solved only for the first angle being 90°.')],
        f'The sine of an angle equals the cosine of its complement, and the acute angles of a right triangle are complementary. So ({p}x + {q}) + ({rr}x + {s}) = 90, which gives {p + rr}x = {90 - q - s} and x = {x0}.',
        ['How are sin and cos of the two acute angles in a right triangle related?', 'The two acute angles add to 90°.', 'Add the two angle expressions, set the sum equal to 90, and solve.'])


@sat(2, 'circles', 'hard', 'complete the square')
def _circle(r):
    h, k, rad = r.randint(-6, 7), r.randint(-6, 7), r.randint(2, 9)
    if h == 0 or k == 0 or h * h + k * k == rad * rad:
        raise Retry
    eq = f'x² + y² {"+" if -2 * h >= 0 else "−"} {abs(2 * h)}x {"+" if -2 * k >= 0 else "−"} {abs(2 * k)}y {"+" if h * h + k * k - rad * rad >= 0 else "−"} {abs(h * h + k * k - rad * rad)} = 0'
    return spec(f'The equation {eq} defines a circle in the xy-plane with center (h, k) and radius r. What is the value of h + k + r?', h + k + rad, [
        (-h - k + rad, 'Used the opposite signs of the center coordinates.'),
        (h + k + rad * rad, 'Used r² in place of the radius.'),
        (h + k, 'Forgot to add the radius.')],
        f'Complete the square in each variable: ({sub('x', h)})² + ({sub('y', k)})² = {rad * rad}. The center is ({num(h)}, {num(k)}) and the radius is √{rad * rad} = {rad}, so h + k + r = {num(h + k + rad)}.',
        ['Group the x terms and y terms and move the constant to the right side.', 'Add the square of half the linear coefficient to each group and to the right side.', 'Read the center and radius from (x − h)² + (y − k)² = r², then add.'])


@sat(2, 'lines_angles_triangles', 'hard', 'areas of similar triangles')
def _similar_area(r):
    a, b, t = r.choice([2, 3, 4]), r.randint(1, 3), r.randint(2, 5)
    S = a * a * t
    whole = (a + b) ** 2 * t
    return spec(f'In triangle ABC, point D lies on side AB and point E lies on side AC so that DE is parallel to BC. AD = {a * 2} and DB = {b * 2}, and the area of triangle ADE is {S}. What is the area of quadrilateral DBCE?', whole - S, [
        (Fraction(S * (a + b), a), 'Used the ratio of sides instead of the ratio of areas.'),
        (whole, 'Reported the area of the whole triangle.'),
        (S * b // a if (S * b) % a == 0 else Fraction(S * b, a), 'Compared the areas as if they were in the ratio of the sides.')],
        f'Triangles ADE and ABC are similar with side ratio {a}:{a + b}, so their areas are in the ratio {a * a}:{(a + b) ** 2}. Triangle ABC has area {S} × {(a + b) ** 2}/{a * a} = {whole}. The quadrilateral is the difference: {whole} − {S} = {whole - S}.',
        ['Why are triangles ADE and ABC similar?', 'Areas of similar figures scale with the square of the side ratio.', 'Find the area of the large triangle, then subtract the small one.'])


# ------------------------------------------------------ Extra practice pool

@extra('sample_inference', 'medium', 'margin of error and plausible values')
def _plausible(r):
    n, p, m = r.choice([400, 600, 900, 1200]), r.randint(38, 62), r.randint(2, 5)
    inside = r.randint(p - m + 1, p + m - 1)
    return spec(f'A random sample of {n} residents found that {p}% favor a new park. The margin of error for the estimate is {m} percentage points. Which of the following is a plausible value of the percentage of all residents who favor the park?', f'{inside}%', [
        (f'{p + m + 2}%', 'Chose a value above the interval.'),
        (f'{p - m - 3}%', 'Chose a value below the interval.'),
        (f'{p + 2 * m}%', 'Doubled the margin of error.')],
        f'The plausible values run from {p - m}% to {p + m}%. Only {inside}% is inside that interval.',
        ['A margin of error creates an interval around the sample percentage.', 'Compute both endpoints.', 'Choose the value that lies between them.'])


@extra('one_variable_data', 'medium', 'mean of an enlarged data set')
def _new_value(r):
    n, m, m2 = r.randint(4, 8), r.randint(10, 40), 0
    m2 = m + r.choice([-4, -3, 2, 3, 5])
    x = (n + 1) * m2 - n * m
    return spec(f'The mean of {n} numbers is {m}. When a new number is included, the mean of all {n + 1} numbers is {m2}. What is the new number?', x, [
        (m2, 'Reported the new mean.'),
        (m2 + m, 'Added the two means.'),
        (n * m2 - n * m, 'Used the wrong number of values for the new total.')],
        f'The original total is {n} × {m} = {n * m}. The new total is {n + 1} × {m2} = {(n + 1) * m2}. The new number is the difference: {x}.',
        ['Convert each mean into a sum.', 'Total = mean × number of values.', 'The new number is the new total minus the old total.'])


@extra('statistical_claims', 'medium', 'generalizing from a sample')
def _random_sample(r):
    n, place, thing = r.choice([150, 250, 500]), r.choice(['a large school district', 'a mid-sized town', 'a county']), r.choice(['a longer school day', 'a new bus schedule', 'more bike lanes'])
    return spec(f'A researcher randomly selected {n} residents of {place} and asked whether they support {thing}. Which conclusion is best supported?', f'The percentage of all residents of {place} who support {thing} can be reasonably estimated from the sample.', [
        (f'Support for {thing} in every other community can be estimated from the sample.', 'Generalized beyond the sampled population.'),
        (f'{thing.capitalize()} causes residents to support it more.', 'Claimed cause from a survey.'),
        ('No estimate is possible because only some residents were surveyed.', 'Rejected sampling altogether.')],
        f'A random sample allows an estimate for the population it was drawn from: here, {place}. It does not extend to other populations, and a survey cannot show cause.',
        ['Who was the sample drawn from?', 'Random selection supports generalizing to that population only.', 'A survey asks opinions; it does not test a cause.'])


@extra('area_volume', 'hard', 'composite volume')
def _cylinder_fill(r):
    rad, h, c = r.randint(3, 8), r.randint(5, 12), r.choice([2, 3, 4, 6, 9])
    if (rad * rad * h) % c:
        raise Retry
    return spec(f'A cylindrical tank has a radius of {rad} feet and a height of {h} feet. Water flows into the empty tank at a rate of {c}π cubic feet per minute. How many minutes does it take to fill the tank?', Fraction(rad * rad * h, c), [
        (Fraction((2 * rad) ** 2 * h, c), 'Used the diameter as the radius.'),
        (Fraction(rad * h, c), 'Did not square the radius.'),
        (rad * rad * h, 'Gave the volume divided by π instead of dividing by the fill rate.')],
        f'The volume is π({rad})²({h}) = {rad * rad * h}π cubic feet. Dividing by {c}π cubic feet per minute gives {num(Fraction(rad * rad * h, c))} minutes.',
        ['Find the volume of the tank in terms of π.', 'Time = volume ÷ rate.', 'The π factors cancel.'])


@extra('right_triangles_trig', 'hard', 'trig ratios in context')
def _angle_of_elevation(r):
    a, b, h = r.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17)])
    k = r.randint(5, 12)
    return spec(f'From a point on level ground, the angle of elevation to the top of a tower has a sine of {a}/{h}. The straight-line distance from the point to the top of the tower is {k * h} meters. How tall is the tower, in meters?', k * a, [
        (k * b, 'Used the adjacent side.'),
        (k * h, 'Used the hypotenuse.'),
        (Fraction(k * h * h, a), 'Divided instead of multiplying by the sine.')],
        f'Sine is opposite over hypotenuse, so the tower height is {k * h} × {a}/{h} = {k * a} meters.',
        ['Sketch the right triangle and label the tower as the side opposite the angle.', 'Sine relates the opposite side to the hypotenuse.', 'Multiply the hypotenuse by the sine.'])


@extra('function_notation', 'medium', 'evaluate and solve')
def _solve_function(r):
    m, b, x0 = r.randint(2, 7), r.randint(-9, 9), r.randint(2, 9)
    target = m * x0 * x0 + b
    return spec(f'The function f is defined by f(x) = {poly({2: m, 0: b})}. For a positive value of a, f(a) = {target}. What is the value of a?', x0, [
        (-x0, 'Gave the negative solution.'),
        (x0 * x0, 'Reported a².'),
        (target - b, 'Subtracted b but did not divide by the coefficient.')],
        f'Set {poly({2: m, 0: b}, "a")} = {target}, so {m}a² = {target - b} and a² = {x0 * x0}. The positive solution is a = {x0}.',
        ['Substitute a into the function and set the result equal to the output.', 'Isolate the squared term.', 'Take the positive square root.'])
