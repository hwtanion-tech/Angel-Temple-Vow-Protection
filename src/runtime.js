/* Runtime-only eligibility, deliberately separate from anatomical history. */
(() => {
  "use strict";
  let active = true;
  const ranks = new Set(["prospective", "initiate", "monk", "priest"]);

  function maintainVow() {
    if (typeof State === "undefined" || !State.variables) return;
    const v = State.variables;
    // Migrate only this mod's obsolete flag; never alter anatomical records.
    delete v.angelTempleVowProtection;
    if (active && ranks.has(v.temple_rank) && v.player?.virginity) {
      v.player.virginity.temple = true;
    }
  }

  window.AngelTempleVowProtection = Object.freeze({
    version: "2.2.0",
    enabled: () => active,
    // Session-only diagnostic switch, not a new saved gameplay setting.
    setEnabled(value) {
      active = value === true;
      maintainVow();
    },
    maintainVow,
  });

  $(document).on(":passagestart.angelTempleVowProtection :storyready.angelTempleVowProtection", maintainVow);
  maintainVow();
})();
