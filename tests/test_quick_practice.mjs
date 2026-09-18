import assert from 'node:assert/strict'
import { drillBanks, makeRound } from '../frontend/src/quick-practice-data.js'
for (const exam of ['sat', 'act']) {
  for (const subject of ['math', 'ela']) {
    for (const question of drillBanks[exam][subject]) {
      assert.equal(new Set(question.options).size, 4, question.prompt)
      assert.ok(question.answer >= 0 && question.answer < 4)
      assert.ok(question.explanation && question.tip)
      if (subject === 'math') {
        const numbers = question.prompt.match(/\d+/g).map(Number)
        let expected
        if (question.skill === 'Backsolve') expected = (numbers[2] - numbers[1]) / numbers[0]
        if (question.skill === 'Percent multipliers') expected = `$${numbers[0] * (1 - numbers[1] / 100)}`
        if (question.skill === 'Read the target') expected = (numbers[2] - numbers[1]) / numbers[0] * numbers[3]
        if (question.skill === 'Rate setup') expected = numbers[0] / numbers[1] * numbers[2]
        if (question.skill === 'Average shortcut') expected = numbers[0] * 4 - numbers.slice(1).reduce((a, b) => a + b, 0)
        if (expected !== undefined) assert.equal(question.options[question.answer], String(expected), question.prompt)
      }
    }
    for (let i = 0; i < 50; i++) {
      const round = makeRound(exam, subject)
      assert.equal(round.length, 5)
      assert.equal(new Set(round.map(question => question.skill)).size, 5)
      for (const question of round) {
        const original = drillBanks[exam][subject].find(item => item.prompt === question.prompt)
        assert.equal(question.options[question.answer], original.options[original.answer])
      }
    }
  }
}
console.log('All practice banks and 200 randomized rounds passed.')
