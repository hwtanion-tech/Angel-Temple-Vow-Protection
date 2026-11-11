"""Small, explicit eligibility edits; no global replacement of virginity data."""

API = "window.AngelTempleVowProtection.enabled()"
VIRGIN = "$player.virginity.penile is true and $player.virginity.vaginal is true"
LOST = "$player.virginity.penile isnot true or $player.virginity.vaginal isnot true"
VOW = "$player.virginity.temple is true"
DAILY = "if (V.player.virginity.vaginal === true && V.player.virginity.penile === true) dailyPurity += 2;"
DAILY_NEW = f"if ({API} || (V.player.virginity.vaginal === true && V.player.virginity.penile === true)) dailyPurity += 2;"
MAX = "const max = V.virginityProtected || (V.player.virginity.vaginal === true && V.player.virginity.penile === true) ? 1000 : 999;"
MAX_NEW = f"const max = {API} || V.virginityProtected || (V.player.virginity.vaginal === true && V.player.virginity.penile === true) ? 1000 : 999;"


def event_rules():
    rules = []

    def add(passage, old, new, expected=1):
        rules.append((passage, old, new, expected))

    def condition(passage, old, new, kind="if", expected=1):
        add(passage, f"<<{kind} {old}>>", f"<<{kind} {new}>>", expected)

    condition("Temple Test", VIRGIN, f"{API} or ({VIRGIN})", expected=2)
    for passage in ["Temple Test", "Sydney Temple Pure Test"]:
        condition(passage, f"{VIRGIN} or {VOW}", f"{API} or ({VIRGIN}) or {VOW}")
    condition("Sydney Temple Test 2",
              f"(_sydneyVirgin and {VIRGIN}) or ({VOW} and C.npc.Sydney.virginity.temple is true)",
              f"(_sydneyVirgin and {VIRGIN}) or (({VOW} or {API}) and C.npc.Sydney.virginity.temple is true)")
    condition("Brothel Show Virginity Examination", VIRGIN, f"{API} or ({VIRGIN})")
    condition("Briar's Office Show",
              f"$brothelVirginityIntro is undefined and ({VIRGIN}) and !unableTakeVirginity() and fameSum('sex', 'prostitution', 'rape') gte 100",
              f"$brothelVirginityIntro is undefined and ({API} or (({VIRGIN}) and !unableTakeVirginity())) and fameSum('sex', 'prostitution', 'rape') gte 100")
    condition("Widgets Brothel",
              f'$brothelVirginityIntro is true and $brothelVirginityState isnot "lie" and ({VIRGIN}) and !unableTakeVirginity()',
              f'$brothelVirginityIntro is true and $brothelVirginityState isnot "lie" and ({API} or (({VIRGIN}) and !unableTakeVirginity()))')
    condition("Brothel Show", LOST, f"not {API} and ({LOST})", kind="elseif")
    # Replace only the expression prefix, not translated narrative or effects.
    add("Brothel Show Virginity Intro", f"<<= {VIRGIN} ?", f"<<= ({API} or ({VIRGIN})) ?")
    condition("Brothel Show Virginity Stage", LOST, f"not {API} and ({LOST})")
    for passage in ["Underground Intro", "Underground Intro2"]:
        condition(passage, VIRGIN, f"{API} or ({VIRGIN})")
    condition("Underground Intro",
              '($player.vaginaExist and !unableTakeVirginity("vaginal")) or ($player.penisExist and !unableTakeVirginity("penile"))',
              f'($player.vaginaExist and ({API} or !unableTakeVirginity("vaginal"))) or ($player.penisExist and ({API} or !unableTakeVirginity("penile")))')
    condition("Temple Chastity", VIRGIN, f"{API} or ({VIRGIN})", kind="elseif")
    condition("Temple Chastity", f"playerChastity() and {VIRGIN} and !playerBellyVisible()",
              f"playerChastity() and ({API} or ({VIRGIN})) and !playerBellyVisible()")
    condition("Mansion Talk Chat 2",
              '$rng is 2 and !$avery_fate and $player.virginity.vaginal is true and $player.virginity.penile is true and $player.virginity.temple is true and !$averySeen.includes("player_virgin")',
              f'$rng is 2 and !$avery_fate and ({API} or ($player.virginity.vaginal is true and $player.virginity.penile is true)) and $player.virginity.temple is true and !$averySeen.includes("player_virgin")', kind="elseif")
    add("Virginity Show Test", f'<<= !unableTakeVirginity() and {VIRGIN} ? "true" : "false">>',
        f'<<= ({API} or (!unableTakeVirginity() and {VIRGIN})) ? "true" : "false">>')
    condition("Adult Shop Widgets", f"$angel gte 4 or {VIRGIN} or $player.temple_virginity is true",
              f"$angel gte 4 or {API} or ({VIRGIN}) or $player.temple_virginity is true")
    condition("Doctor Harper's Office Camera Molestation",
              '($player.virginity.vaginal isnot true or $player.virginity.penile isnot true) and $templePromised is ""',
              f'not {API} and ($player.virginity.vaginal isnot true or $player.virginity.penile isnot true) and $templePromised is ""')
    return rules


def core_rules():
    opener = '<<widget "fallenTransform">>'
    boundary = '<</widget>>\n\n<<widget "fallenButNotOut">>'
    vow_prefix = '<<if $player.virginity.temple is true and (_args[1] is "vaginal" or _args[1] is "penile")'
    purity_prefix = '<<case "vaginal" "penile">>\n\t\t\t\t\t\t<<if $templePromised isnot $_taker'
    sidebar = '<<run T.buttons = new window.Tab("overlayButtons", "macro-button-selected")>>'
    return [
        ("Transformation Widgets", opener, opener + f"<<if not {API}>>", 1),
        ("Transformation Widgets", boundary, "<</if>>" + boundary, 1),
        ("Widgets Combat", vow_prefix, f"<<if not {API} and " + vow_prefix[5:], 2),
        ("Widgets Combat", purity_prefix, purity_prefix.replace("<<if ", f"<<if not {API} and "), 1),
        ("StoryCaption", sidebar, sidebar + "\n<<run window.AngelTempleVowProtection.maintainVow()>>", 1),
        ("Traits", DAILY, DAILY_NEW, 2),
    ]
