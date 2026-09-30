"""ACT-length Math benchmark: 45 questions ordered easy to hard, as on the test.

Content covers the published ACT categories: number and quantity, algebra,
functions, geometry, statistics and probability, and the trigonometry and
"preparing for higher math" topics. Every answer is computed.
"""
import math
from fractions import Fraction
from itertools import combinations, permutations

import bench_sat_math as sat_math
from bench_common import Retry, num, pi_form, poly, register, spec

ACT_MATH = []
PA, CO, PG, TR = 'act_math_prealgebra', 'act_math_coordinate', 'act_math_plane_geometry', 'act_math_trig'


def act(skill, difficulty, sub):
    return register(ACT_MATH, 1, skill, difficulty, sub)


def reuse(fn, skill, difficulty, sub):
    register(ACT_MATH, 1, skill, difficulty, sub)(fn)


def tup(x, y):
    return f'({num(x)}, {num(y)})'


TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (6, 8, 10), (7, 24, 25)]


@act(PA, 'easy', 'fraction arithmetic')
def _fractions(r):
    p, q, rr, s, t, u = r.choice([1, 2, 3]), r.choice([4, 5, 6]), 1, r.choice([2, 3]), r.choice([1, 2]), r.choice([3, 4])
    a, b, c = Fraction(p, q), Fraction(rr, s), Fraction(t, u)
    if b == c:
        raise Retry
    return spec(f'What is the value of {p}/{q} ÷ {rr}/{s} − {t}/{u}?', a / b - c, [
        (a * b - c, 'Multiplied by the second fraction instead of dividing.'),
        (a / b + c, 'Added the last fraction instead of subtracting.'),
        (a / (b - c), 'Applied the subtraction before the division.')],
        f'Dividing by {rr}/{s} is multiplying by {s}/{rr}: {p}/{q} × {s}/{rr} = {num(a / b)}. Subtracting {t}/{u} leaves {num(a / b - c)}.',
        ['Follow the order of operations: division comes before subtraction.', 'Dividing by a fraction means multiplying by its reciprocal.', 'Rewrite with a common denominator before subtracting.'])


reuse(sat_math._discount_tax, PA, 'easy', 'successive percent change')


@act(PA, 'easy', 'rates and unit rates')
def _gas(r):
    m, g, g2 = r.choice([24, 25, 28, 30, 32, 36]), r.choice([6, 8, 10, 12]), r.choice([15, 18, 20, 25])
    d, D = m * g, m * g2
    return spec(f'A car travels {d} miles on {g} gallons of gasoline. At this rate, how many gallons are needed to travel {D} miles?', g2, [
        (g2 - g, 'Found only the gallons for the additional miles.'),
        (Fraction(D, g), 'Divided the miles by the gallons of the first trip.'),
        (g2 + g, 'Added the two gallon amounts.')],
        f'The car gets {d}/{g} = {m} miles per gallon. For {D} miles it needs {D}/{m} = {g2} gallons.',
        ['Find the unit rate first.', 'Miles per gallon stays the same on both trips.', 'Divide the new distance by the miles per gallon.'])


reuse(sat_math._exterior, PG, 'easy', 'exterior angles')


@act(CO, 'easy', 'slope')
def _slope(r):
    x1, y1 = r.randint(-5, 5), r.randint(-6, 6)
    dx, dy = r.choice([2, 3, 4, 5]), r.choice([-7, -5, -3, -2, 2, 3, 4, 6])
    x2, y2 = x1 + dx, y1 + dy
    m = Fraction(dy, dx)
    return spec(f'What is the slope of the line through the points {tup(x1, y1)} and {tup(x2, y2)}?', m, [
        (Fraction(dx, dy), 'Inverted the slope: run over rise.'),
        (-m, 'Subtracted the coordinates in opposite orders.'),
        (Fraction(y1 + y2, x1 + x2) if x1 + x2 else 0, 'Added the coordinates instead of subtracting.')],
        f'Slope is rise over run: ({num(y2)} − {num(y1)}) / ({num(x2)} − {num(x1)}) = {num(dy)}/{dx}, which simplifies to {num(m)}. Subtracting the coordinates in the same order in both parts keeps the sign correct.',
        ['Slope compares the change in y to the change in x.', 'Subtract the coordinates in the same order in the numerator and denominator.', 'Write rise over run and simplify.'])


reuse(sat_math._rectangle, PG, 'easy', 'perimeter and area')
reuse(sat_math._distribute, PA, 'easy', 'solving linear equations')


@act(CO, 'easy', 'midpoint')
def _midpoint(r):
    ax, ay, mx, my = r.randint(-8, 6), r.randint(-8, 6), r.randint(-4, 8), r.randint(-4, 8)
    bx, by = 2 * mx - ax, 2 * my - ay
    return spec(f'The midpoint of segment AB is {tup(mx, my)}. Point A has coordinates {tup(ax, ay)}. What are the coordinates of point B?', tup(bx, by), [
        (tup(mx - ax, my - ay), 'Treated the midpoint as a displacement.'),
        (tup(mx + ax, my + ay), 'Added the midpoint and the endpoint.'),
        (tup(bx, my - ay), 'Applied the midpoint relationship to only one coordinate.')],
        f'The midpoint is the average of the endpoints, so each coordinate of B is twice the midpoint coordinate minus the coordinate of A: ({2 * mx} − {num(ax)}, {2 * my} − {num(ay)}) = {tup(bx, by)}.',
        ['The midpoint is the average of the two endpoints.', 'Work with the x-coordinates and y-coordinates separately.', 'Solve (ax + bx)/2 = mx for bx, then do the same for y.'])


reuse(sat_math._flip, PA, 'easy', 'linear inequalities')
reuse(sat_math._absolute, PA, 'medium', 'absolute value equations')


@act(PA, 'medium', 'scientific notation')
def _scientific(r):
    a, b, m, n = r.randint(2, 9), r.randint(2, 9), r.randint(2, 6), r.choice([-4, -3, -2, 2, 3, 4])
    if a * b < 10 or m == n:
        raise Retry
    p = a * b
    mant = f'{p / 10:g}'
    return spec(f'What is the value of ({a} × 10^{num(m)})({b} × 10^{num(n)}) written in scientific notation?', f'{mant} × 10^{num(m + n + 1)}', [
        (f'{p} × 10^{num(m + n)}', 'Left the coefficient outside the range of scientific notation.'),
        (f'{mant} × 10^{num(m + n)}', 'Changed the coefficient without adjusting the exponent.'),
        (f'{mant} × 10^{num(m * n + 1)}', 'Multiplied the exponents instead of adding them.')],
        f'Multiply the coefficients and add the exponents: {a} × {b} = {p} and 10^{num(m)} × 10^{num(n)} = 10^{num(m + n)}. So the product is {p} × 10^{num(m + n)}. To be in scientific notation, write {p} as {mant} × 10, making the exponent {num(m + n + 1)}.',
        ['Multiply the coefficients and the powers of ten separately.', 'When multiplying powers of the same base, add the exponents.', 'Scientific notation needs a coefficient between 1 and 10; adjust the exponent when you fix it.'])


@act(PG, 'medium', 'Pythagorean theorem')
def _diagonal(r):
    a, b, h = r.choice(TRIPLES)
    k = r.randint(1, 4)
    return spec(f'A rectangle has side lengths of {a * k} inches and {b * k} inches. What is the length, in inches, of its diagonal?', h * k, [
        (k * (a + b), 'Added the two side lengths.'),
        (Fraction(a * b * k * k, h), 'Divided the area by the hypotenuse of the ratio triangle.'),
        ((a * a + b * b) * k * k, 'Added the squares and forgot the square root.')],
        f'The diagonal is the hypotenuse of a right triangle with legs {a * k} and {b * k}: √({a * k}² + {b * k}²) = √{(a * a + b * b) * k * k} = {h * k}.',
        ['The diagonal and two sides of a rectangle form a right triangle.', 'Use the Pythagorean theorem a² + b² = c².', 'Take the square root after adding the squares.'])


@act(CO, 'medium', 'distance formula')
def _distance(r):
    a, b, h = r.choice(TRIPLES)
    k = r.randint(1, 3)
    x1, y1 = r.randint(-6, 4), r.randint(-6, 4)
    sx, sy = r.choice([1, -1]), r.choice([1, -1])
    x2, y2 = x1 + sx * a * k, y1 + sy * b * k
    return spec(f'What is the distance between the points {tup(x1, y1)} and {tup(x2, y2)} in the standard (x, y) coordinate plane?', h * k, [
        ((a + b) * k, 'Added the horizontal and vertical distances.'),
        (h * k * h * k, 'Forgot the final square root.'),
        (max(a, b) * k, 'Reported the longer leg.')],
        f'The horizontal distance is {a * k} and the vertical distance is {b * k}. The distance formula gives √({a * k}² + {b * k}²) = {h * k}.',
        ['The distance formula comes from the Pythagorean theorem.', 'Find the horizontal and vertical differences.', 'Square each, add, and take the square root.'])


reuse(sat_math._new_value, PA, 'medium', 'mean of a changed data set')
reuse(sat_math._ratio_change, PA, 'medium', 'ratios')


@act(PG, 'medium', 'similar triangles')
def _shadows(r):
    h1, s1 = r.choice([(6, 4), (5, 2), (6, 9), (4, 6)])
    g = math.gcd(h1, s1)
    s2 = (s1 // g) * r.randint(4, 9)
    h2 = Fraction(h1 * s2, s1)
    return spec(f'A {h1}-foot-tall person casts a shadow that is {s1} feet long. At the same time, a flagpole casts a shadow that is {s2} feet long. How tall, in feet, is the flagpole?', h2, [
        (Fraction(s1 * s2, h1), 'Set up the proportion upside down.'),
        (h1 + s2 - s1, 'Added the difference in shadow lengths to the height.'),
        (s2, 'Assumed the flagpole’s height equals its shadow.')],
        f'The sun makes similar right triangles, so height/shadow is the same: {h1}/{s1} = h/{s2}. So h = {h1} × {s2} / {s1} = {num(h2)} feet.',
        ['The person and the flagpole with their shadows form similar triangles.', 'Corresponding sides are proportional: height to shadow.', 'Cross-multiply and solve for the flagpole’s height.'])


@act(PG, 'medium', 'polygon angles')
def _polygon(r):
    n = r.choice([5, 6, 8, 9, 10, 12])
    theta = Fraction(180 * (n - 2), n)
    return spec(f'Each interior angle of a regular polygon measures {num(theta)}°. How many sides does the polygon have?', n, [
        (Fraction(360, theta), 'Divided 360° by the interior angle instead of the exterior angle.'),
        (n - 2, 'Reported the number of triangles, not sides.'),
        (n + 1, 'Miscounted by one when using the exterior angle.')],
        f'Each exterior angle is 180° − {num(theta)}° = {num(180 - theta)}°. The exterior angles of any polygon sum to 360°, so the number of sides is 360/{num(180 - theta)} = {n}.',
        ['Interior and exterior angles at a vertex add to 180°.', 'The exterior angles of any polygon add to 360°.', 'Divide 360° by one exterior angle.'])


@act(PA, 'medium', 'weighted averages and mixtures')
def _mixture(r):
    A, B, p, q = r.randint(2, 8), r.randint(2, 8), r.choice([10, 15, 20, 25, 30]), r.choice([40, 50, 60, 70, 80])
    v = Fraction(A * p + B * q, A + B)
    if v.denominator > 2 or A == B:
        raise Retry
    return spec(f'A chemist mixes {A} liters of a {p}% acid solution with {B} liters of a {q}% acid solution. What is the acid concentration of the mixture, in percent?', v, [
        (Fraction(p + q, 2), 'Averaged the two percents without weighting by volume.'),
        (Fraction(B * p + A * q, A + B), 'Swapped the volumes when weighting.'),
        (p + q, 'Added the percents.')],
        f'Acid in the mixture: {A}({p}/100) + {B}({q}/100) = {num(Fraction(A * p + B * q, 100))} liters out of {A + B} liters. As a percent that is {num(v)}%.',
        ['Different volumes mean a simple average will not work.', 'Find the amount of pure acid from each solution.', 'Divide the total acid by the total volume.'])


@act(CO, 'medium', 'intercepts from two points')
def _xint(r):
    m, xi = r.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]), r.randint(-6, 8)
    x1, x2 = r.sample([v for v in range(-7, 10) if v != xi], 2)
    y1, y2 = m * (x1 - xi), m * (x2 - xi)
    return spec(f'A line in the standard (x, y) coordinate plane passes through {tup(x1, y1)} and {tup(x2, y2)}. At what x-coordinate does the line cross the x-axis?', xi, [
        (-m * xi, 'Reported the y-intercept.'),
        (-xi, 'Made a sign error solving for the intercept.'),
        (Fraction(-y1, m) if m else 0, 'Divided the y-value by the slope without adding the x-coordinate.')],
        f'The slope is ({num(y2)} − {num(y1)})/({x2} − {num(x1)}) = {m}. Setting y = 0 in y − {num(y1)} = {m}(x − {num(x1)}) gives x = {xi}.',
        ['Find the slope using the two points.', 'Write the line’s equation using one of the points.', 'Set y = 0 and solve for x.'])


@act(PA, 'medium', 'permutations')
def _perm(r):
    n = r.randint(7, 12)
    return spec(f'A club of {n} members will choose a president, a vice president, and a treasurer. No member can hold more than one office. In how many different ways can the offices be filled?', n * (n - 1) * (n - 2), [
        (len(list(combinations(range(n), 3))), 'Counted groups of three and ignored the order of the offices.'),
        (n ** 3, 'Allowed the same member to hold more than one office.'),
        (3 * n, 'Multiplied by the number of offices instead of counting choices.')],
        f'There are {n} choices for president, then {n - 1} for vice president, then {n - 2} for treasurer: {n} × {n - 1} × {n - 2} = {n * (n - 1) * (n - 2)}.',
        ['Does the order in which members are chosen matter here?', 'Each office is filled in turn from those who remain.', 'Multiply the number of choices for each office.'])


@act(PA, 'medium', 'combinations')
def _comb(r):
    n = r.randint(7, 12)
    return spec(f'A teacher will choose 3 students from a group of {n} students to represent the class. In how many different ways can the 3 students be chosen?', len(list(combinations(range(n), 3))), [
        (n * (n - 1) * (n - 2), 'Counted ordered selections.'),
        (len(list(combinations(range(n), 2))), 'Chose 2 students instead of 3.'),
        (n * 3, 'Multiplied the group size by 3.')],
        f'The order of the three students does not matter, so use combinations: {n}!/(3!({n} − 3)!) = {num(len(list(combinations(range(n), 3))))}.',
        ['Does choosing Ana, Ben, Cy differ from choosing Cy, Ben, Ana?', 'If order does not matter, divide the ordered count by the number of ways to arrange the group.', 'Compute n(n − 1)(n − 2)/(3 × 2 × 1).'])


reuse(sat_math._tangent, TR, 'medium', 'right triangle trigonometry')


@act(PA, 'medium', 'probability without replacement')
def _marbles(r):
    red, blue = r.randint(3, 8), r.randint(2, 7)
    n = red + blue
    p = Fraction(red * (red - 1), n * (n - 1))
    return spec(f'A bag contains {red} red marbles and {blue} blue marbles. Two marbles are drawn at random, one after the other, without replacement. What is the probability that both marbles are red?', p, [
        (Fraction(red * red, n * n), 'Used the same total for both draws.'),
        (Fraction(red * (red - 1), n * n), 'Reduced the red count but not the total.'),
        (Fraction(red, n) + Fraction(red - 1, n - 1), 'Added the two probabilities instead of multiplying.')],
        f'The first marble is red with probability {red}/{n}. Then {red - 1} red marbles remain among {n - 1}, so the second is red with probability {red - 1}/{n - 1}. The probability of both is {num(p)}.',
        ['Drawing without replacement changes the bag after the first draw.', 'Multiply the probabilities of the two dependent events.', 'After one red marble is removed, both the red count and the total drop by one.'])


reuse(sat_math._parallel, CO, 'medium', 'parallel lines')
reuse(sat_math._arc, PG, 'medium', 'arc length')
reuse(sat_math._x_plus_y, CO, 'medium', 'systems of equations')


@act(PA, 'medium', 'exponent rules')
def _exponent_eq(r):
    b, s, x0 = r.choice([2, 3]), r.choice([2, 3]), r.randint(2, 4)
    R = (b ** s - 1) * b ** x0
    return spec(f'If {b}^(x + {s}) − {b}^x = {R}, what is the value of x?', x0, [
        (b ** x0, 'Reported the value of the power instead of the exponent.'),
        (x0 + s, 'Added the shift to the exponent.'),
        (x0 + 1, 'Miscounted the exponent by one.')],
        f'Factor out {b}^x: {b}^x({b}^{s} − 1) = {R}, so {b}^x({b ** s - 1}) = {R} and {b}^x = {b ** x0}. Therefore x = {x0}.',
        ['Rewrite b^(x + s) using the product rule for exponents.', 'Factor the common power out of both terms.', 'Once you have b^x equal to a number, decide what exponent produces it.'])


@act(TR, 'medium', 'exact trigonometric values')
def _exact(r):
    bank = [('sin 30°', Fraction(1, 2)), ('cos 60°', Fraction(1, 2)), ('tan 45°', Fraction(1)), ('sin 90°', Fraction(1)),
            ('cos 0°', Fraction(1)), ('cos 90°', Fraction(0)), ('sin 0°', Fraction(0)), ('cos 180°', Fraction(-1)),
            ('sin 150°', Fraction(1, 2)), ('cos 120°', Fraction(-1, 2)), ('sin 270°', Fraction(-1))]
    (n1, v1), (n2, v2), (n3, v3) = r.sample(bank, 3)
    return spec(f'What is the value of {n1} + {n2} − {n3}?', v1 + v2 - v3, [
        (v1 - v2 + v3, 'Applied the signs to the wrong terms.'),
        (v1 + v2 + v3, 'Ignored the subtraction.'),
        (v1 * v2 - v3, 'Multiplied instead of adding.')],
        f'{n1} = {num(v1)}, {n2} = {num(v2)}, and {n3} = {num(v3)}. So {num(v1)} + {num(v2)} − ({num(v3)}) = {num(v1 + v2 - v3)}.',
        ['Recall the exact values from the unit circle.', 'Watch the quadrant for the sign.', 'Substitute each value, then combine them carefully.'])


reuse(sat_math._compose, CO, 'medium', 'function composition')


@act(PG, 'medium', 'scaling similar solids')
def _scale_volume(r):
    a, b, t = r.choice([(2, 3), (2, 5), (3, 4), (3, 5), (1, 3), (2, 7)]), 0, r.randint(2, 6)
    a, b = a
    V = t * a ** 3
    return spec(f'Two similar rectangular boxes have corresponding edge lengths in the ratio {a}:{b}. The volume of the smaller box is {V} cubic inches. What is the volume, in cubic inches, of the larger box?', t * b ** 3, [
        (t * a * b * b, 'Scaled the volume by the ratio of areas.'),
        (t * a * a * b, 'Scaled the volume by the ratio of lengths.'),
        (V + b ** 3 - a ** 3, 'Added the difference of the cubes of the edges.')],
        f'Volumes of similar solids scale with the cube of the edge ratio: ({b}/{a})³ = {b ** 3}/{a ** 3}. So the larger volume is {V} × {b ** 3}/{a ** 3} = {t * b ** 3}.',
        ['Lengths, areas and volumes scale differently for similar solids.', 'Volume scales by the cube of the length ratio.', 'Cube the ratio and multiply by the smaller volume.'])


@act(PA, 'hard', 'logarithms')
def _logs(r):
    i, j, k = r.randint(2, 6), r.randint(2, 4), r.randint(1, 3)
    return spec(f'What is the value of log₂ {2 ** i} + log₃ {3 ** j} − log₅ {5 ** k}?', i + j - k, [
        (i + j + k, 'Added the last logarithm instead of subtracting it.'),
        (i * j - k, 'Multiplied the first two logarithms.'),
        (2 ** i + 3 ** j - 5 ** k, 'Added and subtracted the arguments instead of evaluating the logarithms.')],
        f'log₂ {2 ** i} = {i}, log₃ {3 ** j} = {j}, and log₅ {5 ** k} = {k}, because each argument is the base raised to that power. So the value is {i} + {j} − {k} = {i + j - k}.',
        ['log_b(n) asks: to what power must b be raised to get n?', 'Rewrite each argument as a power of its base.', 'Evaluate each logarithm, then combine them.'])


reuse(sat_math._max_height, CO, 'hard', 'quadratic models')
reuse(sat_math._circle, CO, 'hard', 'equations of circles')


@act(PA, 'hard', 'arithmetic sequences')
def _arith(r):
    d, a1 = r.choice([-4, -3, -2, 2, 3, 4, 5, 6]), r.randint(-9, 15)
    A, B = a1 + 3 * d, a1 + 8 * d
    return spec(f'In an arithmetic sequence, the 4th term is {A} and the 9th term is {B}. What is the 20th term?', a1 + 19 * d, [
        (a1 + 20 * d, 'Used 20 steps from the first term instead of 19.'),
        (a1 + 18 * d, 'Used 18 steps from the first term.'),
        (A + 20 * d, 'Added 20 common differences to the 4th term.')],
        f'The common difference is ({B} − {num(A)})/(9 − 4) = {d}. The 20th term is 16 steps after the 4th term: {A} + 16({d}) = {a1 + 19 * d}.',
        ['The terms of an arithmetic sequence change by a constant difference.', 'Use the two known terms to find that difference.', 'Count how many steps separate the known term from the one you want.'])


@act(PG, 'hard', 'cyclic quadrilaterals')
def _cyclic(r):
    x0, p, rr, q = r.randint(8, 25), r.randint(2, 5), r.randint(2, 5), r.randint(1, 20)
    s = 180 - q - (p + rr) * x0
    A, C = p * x0 + q, rr * x0 + s
    if s == 0 or A >= 175 or C >= 175 or A <= 5 or C <= 5:
        raise Retry
    return spec(f'Quadrilateral ABCD is inscribed in a circle. The measure of angle A is ({poly({1: p, 0: q})})° and the measure of angle C is ({poly({1: rr, 0: s})})°. What is the measure of angle A, in degrees?', A, [
        (p * Fraction(360 - q - s, p + rr) + q, 'Used 360° for opposite angles.'),
        (p * Fraction(90 - q - s, p + rr) + q, 'Used 90° for opposite angles.'),
        (x0, 'Stopped after solving for x.')],
        f'Opposite angles of an inscribed quadrilateral are supplementary: ({poly({1: p, 0: q})}) + ({poly({1: rr, 0: s})}) = 180. That gives {p + rr}x + {num(q + s)} = 180, so x = {x0}. Angle A measures {p} × {x0} + {q} = {A}°.',
        ['What is special about opposite angles of a quadrilateral inscribed in a circle?', 'They are supplementary, so their sum is 180°.', 'Write the equation, solve for x, then substitute to find angle A.'])


reuse(sat_math._perpendicular, CO, 'hard', 'perpendicular lines')


@act(PA, 'hard', 'geometric series')
def _geometric(r):
    a, ratio, n = r.randint(2, 7), r.choice([2, 3]), r.randint(5, 6)
    total = a * (ratio ** n - 1) // (ratio - 1)
    return spec(f'The first term of a geometric sequence is {a} and the common ratio is {ratio}. What is the sum of the first {n} terms?', total, [
        (a * ratio ** n, 'Reported the next term instead of the sum.'),
        (a * ratio ** (n - 1), 'Reported only the last term.'),
        (a * (ratio ** n - 1), 'Forgot to divide by ratio − 1.')],
        f'Use S = a(rⁿ − 1)/(r − 1): {a}({ratio}^{n} − 1)/({ratio} − 1) = {total}. You can check by adding {", ".join(str(a * ratio ** i) for i in range(n))}.',
        ['Write out the first few terms to see the pattern.', 'Use the geometric series formula S = a(rⁿ − 1)/(r − 1).', 'Substitute carefully and evaluate the power first.'])


@act(PG, 'hard', 'composite solids')
def _hemisphere(r):
    rad, h = r.choice([3, 6]), r.randint(4, 10)
    V = rad * rad * h + Fraction(2 * rad ** 3, 3)
    return spec(f'A solid is formed by placing a hemisphere of radius {rad} centimeters on top of a cylinder with radius {rad} centimeters and height {h} centimeters. What is the volume of the solid, in cubic centimeters?', pi_form(V), [
        (pi_form(rad * rad * h + Fraction(4 * rad ** 3, 3)), 'Used the volume of a full sphere for the hemisphere.'),
        (pi_form(rad * rad * h), 'Left out the hemisphere.'),
        (pi_form(rad * rad * h + 2 * rad ** 3), 'Forgot the 1/3 in the sphere formula.')],
        f'The cylinder has volume π({rad})²({h}) = {rad * rad * h}π. The hemisphere has half the volume of a sphere: (1/2)(4/3)π({rad})³ = {num(Fraction(2 * rad ** 3, 3))}π. The total is {pi_form(V)}.',
        ['Split the solid into two familiar solids.', 'A hemisphere is half of a sphere: V = (2/3)πr³.', 'Add the two volumes.'])


@act(TR, 'hard', 'law of cosines')
def _law_cosines(r):
    (a, b, c), angle = r.choice([((3, 8, 7), 60), ((5, 8, 7), 60), ((7, 15, 13), 60), ((8, 15, 13), 60), ((3, 5, 7), 120), ((7, 8, 13), 120), ((5, 16, 19), 120)])
    cos_c = Fraction(1, 2) if angle == 60 else Fraction(-1, 2)
    c2 = a * a + b * b - 2 * a * b * cos_c
    assert c2 == c * c
    return spec(f'In triangle ABC, AC = {a}, BC = {b}, and the measure of angle C is {angle}°. What is the length of AB?', c, [
        (a + b, 'Added the two known sides.'),
        (f'√{a * a + b * b}', 'Used the Pythagorean theorem as if angle C were a right angle.'),
        (int(c2), 'Gave AB² instead of AB.')],
        f'By the law of cosines, AB² = {a}² + {b}² − 2({a})({b})cos {angle}° = {a * a + b * b} − {num(2 * a * b * cos_c)} = {c2}. So AB = {c}.',
        ['Two sides and the included angle are known.', 'Use c² = a² + b² − 2ab cos C.', 'Recall cos 60° = 1/2 and cos 120° = −1/2, then take a square root.'])


@act(PA, 'hard', 'complex numbers')
def _complex(r):
    p, q, s, t = r.randint(1, 6), r.choice([-5, -4, -3, -2, 2, 3, 4, 5]), r.randint(1, 5), r.choice([-4, -3, -2, 2, 3, 5])
    re, im = p * s - q * t, p * t + q * s
    def z(a, b):
        return f'{num(a)} {"+" if b >= 0 else "−"} {abs(b)}i'
    return spec(f'For i = √(−1), which of the following is equal to ({z(p, q)})({z(s, t)})?', z(re, im), [
        (z(p * s + q * t, im), 'Treated i² as +1.'),
        (z(re, p * t - q * s), 'Made a sign error in the imaginary part.'),
        (z(p * s, q * t), 'Multiplied the real and imaginary parts separately.')],
        f'Multiply each pair: {p}·{num(s)} + {p}·({num(t)})i + ({num(q)}i)·{num(s)} + ({num(q)}i)({num(t)}i). Since i² = −1, the real part is {p * s} − ({num(q * t)}) = {num(re)} and the imaginary part is {num(im)}.',
        ['Use FOIL, exactly as with binomials.', 'Replace i² with −1.', 'Group the real parts and the imaginary parts.'])


@act(CO, 'hard', 'area of a triangle from coordinates')
def _triangle_area(r):
    x0, y0, a, p, q = r.randint(-5, 3), r.randint(-5, 3), r.randint(4, 10), r.randint(-3, 6), r.randint(3, 9)
    area = Fraction(a * q, 2)
    return spec(f'In the standard (x, y) coordinate plane, triangle ABC has vertices A{tup(x0, y0)}, B{tup(x0 + a, y0)}, and C{tup(x0 + p, y0 + q)}. What is the area of triangle ABC, in square coordinate units?', area, [
        (a * q, 'Forgot the factor of one-half.'),
        (Fraction(abs(p) * a, 2) if p else a, 'Used the horizontal offset of C as the height.'),
        (Fraction(a + q, 2), 'Added the base and the height.')],
        f'Side AB is horizontal with length {a}. The height is the vertical distance from C to line AB: {q}. The area is (1/2)({a})({q}) = {num(area)}.',
        ['Look for a side that is horizontal or vertical.', 'The height is the perpendicular distance from the opposite vertex to that side.', 'Area = (1/2) × base × height.'])


@act(PG, 'hard', '30-60-90 triangles')
def _special_triangle(r):
    h = r.choice([4, 8, 12, 16, 20])
    A = h * h // 8
    return spec(f'A right triangle has angles of 30°, 60°, and 90°, and its hypotenuse is {h} inches long. What is the area of the triangle, in square inches?', f'{A}√3', [
        (f'{A}', 'Left out the radical from the longer leg.'),
        (f'{2 * A}√3', 'Used the wrong leg lengths in the area formula.'),
        (f'{A}√2', 'Used the ratios of a 45°-45°-90° triangle.')],
        f'In a 30°-60°-90° triangle the shorter leg is half the hypotenuse, {h // 2}, and the longer leg is the shorter leg times √3, {h // 2}√3. The area is (1/2)({h // 2})({h // 2}√3) = {A}√3.',
        ['Recall the side ratios 1 : √3 : 2.', 'The hypotenuse is twice the shortest side.', 'Find both legs, then use (1/2)(leg)(leg).'])


@act(TR, 'hard', 'period of a sine function')
def _period(r):
    b, A, c = r.choice([2, 3, 4, 6]), r.randint(2, 6), r.randint(-4, 5)
    return spec(f'What is the period of the function y = {A} sin({b}x){" + " + str(c) if c > 0 else " − " + str(abs(c)) if c < 0 else ""}?', pi_form(Fraction(2, b)), [
        (pi_form(2 * b), 'Multiplied the coefficient by 2π instead of dividing.'),
        (pi_form(Fraction(1, b)), 'Used π instead of 2π in the numerator.'),
        ('2π', 'Used the period of the basic sine function.')],
        f'For y = A sin(bx) + c the period is 2π/|b|. Here b = {b}, so the period is {pi_form(Fraction(2, b))}. The amplitude {A} and the vertical shift {c} do not change the period.',
        ['The period depends only on the coefficient of x.', 'The basic sine function has period 2π.', 'Divide 2π by the coefficient of x.'])


@act(PA, 'hard', 'determinants')
def _matrix(r):
    u, v = r.randint(1, 6), r.randint(2, 8)
    if u == v:
        raise Retry
    s = u - v
    bottom = f'x {"+" if s > 0 else "−"} {abs(s)}'
    return spec(f'A 2 × 2 matrix has the first row (x, {u}) and the second row ({v}, {bottom}). For what positive value of x is the determinant of the matrix equal to 0?', v, [
        (u, 'Reported the opposite of the negative root.'),
        (u * v, 'Reported the product of the roots.'),
        (abs(s), 'Used the constant in the bottom-right entry.')],
        f'The determinant is x({bottom}) − {u}·{v} = x² {"+" if s > 0 else "−"} {abs(s)}x − {u * v}. Setting it to zero gives (x − {v})(x + {u}) = 0, so x = {v} or x = −{u}. The positive value is {v}.',
        ['The determinant of [[a, b], [c, d]] is ad − bc.', 'Set the determinant equal to zero to get a quadratic in x.', 'Solve the quadratic and pick the positive solution.'])


@act(TR, 'hard', 'trigonometric ratios in a quadrant')
def _quadrant(r):
    a, b, h = r.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)])
    return spec(f'If sin θ = {a}/{h} and θ is in Quadrant II, what is the value of tan θ?', Fraction(-a, b), [
        (Fraction(a, b), 'Ignored that tangent is negative in Quadrant II.'),
        (Fraction(-b, a), 'Inverted the ratio.'),
        (Fraction(-a, h), 'Gave the sine with a negative sign.')],
        f'In Quadrant II the sine is positive and the cosine is negative. The reference triangle has legs {a} and {b} and hypotenuse {h}, so cos θ = −{b}/{h}. Then tan θ = sin θ / cos θ = −{a}/{b}.',
        ['Sketch θ in Quadrant II and build a right triangle from the sine.', 'Find the missing side, and assign signs by quadrant.', 'Tangent is sine divided by cosine.'])
