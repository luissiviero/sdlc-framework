const test = require("node:test");
const assert = require("node:assert");
const { add } = require("../src/calc.js");

test("add", () => {
  assert.strictEqual(add(2, 3), 5);
});

test("fails on purpose behind SAMPLE_FAIL=1", () => {
  assert.notStrictEqual(process.env.SAMPLE_FAIL, "1", "SAMPLE_FAIL=1 makes this test fail");
});
