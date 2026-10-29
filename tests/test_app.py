"""Automatiske tester for Studieklokka.

Kjøres med:  python3 tests/test_app.py
Bruker Playwright sin falske klokke, så en 25-minutters økt testes på et sekund.
"""
import json
import pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

APP = pathlib.Path(__file__).resolve().parent.parent / "index.html"
URL = APP.as_uri()
OSLO = ZoneInfo("Europe/Oslo")
NOW = datetime(2026, 10, 28, 12, 0, tzinfo=OSLO)  # onsdag i uke 44

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("BESTÅTT " if cond else "FEILET  ") + name + (f"  ({detail})" if detail and not cond else ""))


def ms(dt):
    return int(dt.timestamp() * 1000)


def advance(page, ms_):
    page.clock.fast_forward(ms_)
    page.clock.run_for(300)


def text(page, sel):
    return page.locator(sel).inner_text().strip()


def new_page(browser, width=1200):
    ctx = browser.new_context(timezone_id="Europe/Oslo", locale="nb-NO", viewport={"width": width, "height": 900})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.clock.install(time=NOW)
    page.goto(URL)
    return ctx, page, errors


with sync_playwright() as p:
    browser = p.chromium.launch()

    # 1. Oppstart
    ctx, page, errors = new_page(browser)
    check("Siden laster uten JavaScript-feil", not errors, "; ".join(errors))
    check("Timeren viser 25:00 ved start", text(page, "#display") == "25:00", text(page, "#display"))
    check("Tom tilstand vises når det ikke finnes økter", page.locator("#empty").is_visible())
    check("Ukenummer vises (uke 44)", text(page, "#weekLabel").lower() == "uke 44", text(page, "#weekLabel"))

    # 2. Velge tid
    page.click(".preset[data-min='45']")
    check("Forhåndsvalg 45 min setter klokka til 45:00", text(page, "#display") == "45:00")
    page.fill("#customMin", "7")
    check("Egen tid 7 min setter klokka til 07:00", text(page, "#display") == "07:00")
    page.fill("#customMin", "")
    page.click(".preset[data-min='25']")

    # 3. Start, pause og fortsett
    page.click("#startBtn")
    advance(page, 10 * 60 * 1000)
    check("Etter 10 min viser klokka 15:00", text(page, "#display") == "15:00", text(page, "#display"))
    page.click("#pauseBtn")
    advance(page, 5 * 60 * 1000)
    check("Pause stopper klokka", text(page, "#display") == "15:00", text(page, "#display"))
    check("Start-knappen heter Fortsett under pause", text(page, "#startBtn") == "Fortsett")
    page.click("#startBtn")
    advance(page, 5 * 60 * 1000)
    check("Fortsett teller videre fra 15:00", text(page, "#display") == "10:00", text(page, "#display"))

    # 4. Oppdatering av siden midt i en økt
    page.reload()
    advance(page, 2 * 60 * 1000)
    check("Timeren overlever at siden lastes på nytt", text(page, "#display") in ("08:00", "07:59"), text(page, "#display"))

    # 5. Ferdig økt legges til sammendraget
    advance(page, 9 * 60 * 1000)
    check("Ferdig økt viser statusmelding", "Ferdig" in text(page, "#status"), text(page, "#status"))
    check("I dag = 25 min etter ferdig økt", text(page, "#sumDay") == "25 min", text(page, "#sumDay"))
    check("Uke = 25 min", text(page, "#sumWeek") == "25 min")
    check("Måned = 25 min", text(page, "#sumMonth") == "25 min")
    check("År = 25 min", text(page, "#sumYear") == "25 min")
    check("Økta står i historikken", page.locator("#history li").count() == 1)

    # 6. Stopp tidlig lagrer faktisk tid, under 1 min lagres ikke
    page.click("#startBtn")
    advance(page, 12 * 60 * 1000)
    page.click("#stopBtn")
    check("Stopp etter 12 min lagrer 12 min", text(page, "#sumDay") == "37 min", text(page, "#sumDay"))
    page.click("#startBtn")
    advance(page, 30 * 1000)
    page.click("#stopBtn")
    check("Stopp etter 30 sek lagres ikke", text(page, "#sumDay") == "37 min", text(page, "#sumDay"))
    check("Melding om at korte økter ikke lagres", "ikke lagret" in text(page, "#status"))

    # 7. Eget fag
    page.fill("#newSubject", "Fysikk")
    page.click("#addSubjectForm button")
    check("Nytt fag blir valgt", page.locator(".chip[aria-pressed='true']").inner_text() == "Fysikk")
    page.fill("#customMin", "1")
    page.click("#startBtn")
    advance(page, 61 * 1000)
    check("Økta får riktig fag i fagoversikten", "Fysikk" in text(page, "#bySubject"), text(page, "#bySubject"))
    page.reload()
    check("Fag og økter er lagret etter omlasting", page.locator(".chip", has_text="Fysikk").count() == 1 and text(page, "#sumDay") == "38 min")

    # 8. Sletting krever to klikk
    first = page.locator("#history li .del").first
    first.click()
    check("Første klikk på Slett ber om bekreftelse", first.inner_text() == "Sikker?")
    first.click()
    check("Andre klikk sletter økta", text(page, "#sumDay") == "37 min", text(page, "#sumDay"))
    ctx.close()

    # 9. Riktig fordeling på dag, uke, måned og år
    ctx, page, errors = new_page(browser)
    data = [
        (datetime(2026, 10, 28, 10, 0, tzinfo=OSLO), 30),   # i dag
        (datetime(2026, 10, 26, 9, 0, tzinfo=OSLO), 60),    # mandag denne uken
        (datetime(2026, 10, 25, 23, 30, tzinfo=OSLO), 45),  # søndag forrige uke
        (datetime(2026, 10, 1, 8, 0, tzinfo=OSLO), 20),     # tidligere i oktober
        (datetime(2026, 9, 15, 8, 0, tzinfo=OSLO), 50),     # september
        (datetime(2025, 12, 31, 20, 0, tzinfo=OSLO), 40),   # i fjor
    ]
    sessions = [{"id": f"t{i}", "start": ms(d), "seconds": m * 60, "planned": m * 60, "subject": "DAVE3625"} for i, (d, m) in enumerate(data)]
    page.evaluate("s => localStorage.setItem('studytimer.sessions.v1', s)", json.dumps(sessions))
    page.reload()
    check("Dag: bare dagens økt (30 min)", text(page, "#sumDay") == "30 min", text(page, "#sumDay"))
    check("Uke: starter mandag (1 t 30 min)", text(page, "#sumWeek") == "1 t 30 min", text(page, "#sumWeek"))
    check("Måned: hele oktober (2 t 35 min)", text(page, "#sumMonth") == "2 t 35 min", text(page, "#sumMonth"))
    check("År: ikke fjoråret (3 t 25 min)", text(page, "#sumYear") == "3 t 25 min", text(page, "#sumYear"))
    check("Streak: 1 dag (søndag til onsdag har hull på tirsdag)", text(page, "#streakNum") == "1", text(page, "#streakNum"))
    check("Ukegrafen har 7 søyler", page.locator("#weekChart rect").count() == 7)

    # 10. Midnatt: dagen nullstilles, uken ikke
    advance(page, 12 * 3600 * 1000 + 1000)
    check("Ved midnatt nullstilles I dag", text(page, "#sumDay") == "0 min", text(page, "#sumDay"))
    check("Ved midnatt beholdes uka", text(page, "#sumWeek") == "1 t 30 min", text(page, "#sumWeek"))
    ctx.close()

    # 11. Eksempeldata
    ctx, page, errors = new_page(browser)
    page.click("#loadSample")
    check("Eksempeldata gir banner", page.locator("#sampleBanner").is_visible())
    check("Eksempeldata gir streak på minst 6 dager", int(text(page, "#streakNum")) >= 6, text(page, "#streakNum"))
    page.click("#clearSample")
    check("Fjern eksempeldata tømmer alt", text(page, "#sumYear") == "0 min" and page.locator("#sampleBanner").is_hidden())
    ctx.close()

    # 12. Mobil
    ctx, page, errors = new_page(browser, width=375)
    page.click("#loadSample")
    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check("Ingen horisontal scrolling på mobil (375 px)", overflow <= 0, f"{overflow}px for bredt")
    page.screenshot(path=str(APP.parent / "tests" / "skjermbilde-mobil.png"), full_page=True)
    ctx.close()

    # Skjermbilde desktop
    ctx, page, errors = new_page(browser)
    page.click("#loadSample")
    page.click(".chip >> nth=0")
    page.click("#startBtn")
    advance(page, 9 * 60 * 1000)
    page.screenshot(path=str(APP.parent / "tests" / "skjermbilde-desktop.png"), full_page=True)
    ctx.close()
    browser.close()

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n{passed}/{len(results)} tester bestått")
raise SystemExit(0 if passed == len(results) else 1)
