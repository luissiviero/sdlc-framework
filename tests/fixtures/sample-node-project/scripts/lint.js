// Stand-in linter for the fixture: fails when a source file contains a tab character.
const fs = require("fs");
const path = require("path");
let bad = 0;
for (const name of fs.readdirSync(path.join(__dirname, "..", "src"))) {
  const text = fs.readFileSync(path.join(__dirname, "..", "src", name), "utf8");
  if (text.includes("\t")) {
    console.error(`${name}: tab character`);
    bad += 1;
  }
}
if (bad) process.exit(1);
console.log("lint ok");
