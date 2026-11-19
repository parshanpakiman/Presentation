"""Verify the static tutorial, numerical widgets, and projected/reading layouts.

Serve the build beneath a repository-style URL prefix and inspect it in isolated
headless Chrome. Check source-independent numerical invariants and meaningful UI
transitions, and save all slide screenshots for visual review.

Key Components:
    - check_models: Verify calculations and prepared research data.
    - check_interactions: Exercise the audience controls and reset behavior.
    - capture_deck: Capture slides and report content/footer overlap.
    - main: Serve, inspect, and write qa/browser-results.json.

Usage Example:
    conda run -n informstutorial python tests/check_browser.py

Notes:
    - Requires installed Chrome and Playwright in informstutorial.
    - Uses no personal browser profile and makes no external service mutations.
"""
from __future__ import annotations

import argparse
import functools
import json
import mimetypes
import threading
from io import BytesIO
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from PIL import Image, ImageDraw
from playwright.sync_api import Page, sync_playwright
import zxingcpp

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "qa"
MAIN_SLIDES = 42
CONTINUOUS_START = 25
CONTINUOUS_DEMOS = 7


class QuietHandler(SimpleHTTPRequestHandler):
    """Serve local build assets without logging each request."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress routine HTTP request logging."""


def check_models(page: Page) -> None:
    """Check physical conservation, action feasibility, density mass, and replay."""
    page.evaluate("""() => {
      const m=TutorialModels, d=TUTORIAL_DATA;
      const check=(v,msg)=>{if(!v)throw new Error(msg);};
      let s=0; [2,1].forEach((a,i)=>{s=m.inventoryCosts(s,a,[5,3][i],false).next;check(s===[-3,-5][i],'zero-stock inventory path');});
      const first=m.inventoryCosts(0,2,5,false), second=m.inventoryCosts(first.next,1,3,false);
      check(first.holding===0&&first.stockout===75&&second.holding===0&&second.stockout===125,'unmet demand carries forward');
      check(first.total+second.total===260,'two-period realized total');
      check(m.sampleInventoryDemand(0,()=>0)===1&&m.sampleInventoryDemand(0,()=>.999)===5,'first demand range');
      check(m.sampleInventoryDemand(1,()=>0)===1&&m.sampleInventoryDemand(1,()=>.999)===5,'second demand range');
      for(let a=0;a<=6;a++)for(let b=0;b<=6;b++)for(let d=1;d<=5;d++)for(let e=1;e<=5;e++){
        const r=m.inventoryCosts(0,a,d,false), t=m.inventoryCosts(r.next,b,e,false);
        check(t.next===a+b-d-e,'intro inventory conservation');
        check(r.stockout===25*r.backlog&&t.stockout===25*t.backlog,'intro stockout rates');
        check(r.lost+t.lost+r.disposal+t.disposal===0,'intro has no hidden lost-sales penalty');
      }
      const shortage=m.inventory(0,0,7);check(shortage.next===-4&&shortage.lost===3,'backlog/lost sales');
      const excess=m.inventory(12,6,0);check(excess.next===12&&excess.disposal===6,'disposal');
      check(m.actions.length===5&&!m.feasible([1,1,0])&&m.feasible([1,0,1]),'feasible actions');
      const f=m.landscape(d.inventory), g=m.gibbs(f,50);
      check(Math.abs(g.reduce((a,b)=>a+b,0)-1)<1e-12,'normalized Gibbs mass');
      check(g.indexOf(Math.max(...g))===f.indexOf(Math.min(...f)),'Gibbs mode');
      check(d.allocation.trace.map(r=>r.objective).join(',')==='0,23.5,49,49','LP replay values');
      d.allocation.trace.forEach(r=>r.weights.forEach(ws=>{
        check(Math.abs(ws.reduce((v,a)=>v+a[1],0)-1)<1e-8,'weight sum');
        ws.forEach(([a])=>check(m.feasible(a),'feasible replay action'));
      }));
    }""")


def check_contents_and_sharing(page: Page, url: str) -> None:
    """Check menu jumps/focus and decode an actual browser-generated QR code."""
    go(page, 1)
    page.wait_for_function('window.CONTENTS_READY')
    trigger = page.locator('.slide-menu-button a')
    assert trigger.is_visible()
    assert trigger.inner_text() == '☰\nContents' or 'Contents' in trigger.inner_text()
    box = trigger.bounding_box()
    assert box['x'] < 35 and box['y'] > 850 and box['height'] <= 35, box
    assert page.locator('.slide-menu-item').count() == MAIN_SLIDES
    assert page.locator('.slide-menu-item-number').first.inner_text() == '01'
    trigger.click()
    page.wait_for_function('Reveal.getPlugin("menu").isOpen()')
    assert trigger.get_attribute('aria-expanded') == 'true'
    page.wait_for_timeout(400)
    page.screenshot(path=str(QA / 'contents-menu.png'))
    page.locator('.slide-menu-item[data-slide-h="22"]').click()
    page.wait_for_function('Reveal.getIndices().h === 22 && !Reveal.getPlugin("menu").isOpen()')
    assert trigger.get_attribute('aria-expanded') == 'false'
    trigger.focus()
    page.keyboard.press('Enter')
    page.wait_for_function('document.activeElement?.getAttribute("data-slide-h") === "22"')
    page.keyboard.press('ArrowDown')
    page.keyboard.press('Enter')
    page.wait_for_function('Reveal.getIndices().h === 23 && !Reveal.getPlugin("menu").isOpen()')
    page.keyboard.press('m')
    page.wait_for_function('Reveal.getPlugin("menu").isOpen()')
    page.keyboard.press('Escape')
    page.wait_for_function('!Reveal.getPlugin("menu").isOpen()')
    assert not page.evaluate('Reveal.isOverview()')
    trigger.click()
    page.locator('.slide-menu-overlay').click(position={'x':1000, 'y':100})
    page.wait_for_function('!Reveal.getPlugin("menu").isOpen()')
    go(page, 1)
    assert page.locator('[data-share-state="placeholder"]').count() == 1
    assert page.locator('[data-share-link]').get_attribute('href') is None
    assert page.evaluate('''() => {
        const authors=document.querySelector('.author-grid').getBoundingClientRect();
        const qr=document.querySelector('.cover-share').getBoundingClientRect();
        const footer=document.querySelector('.projected-footer').getBoundingClientRect();
        return authors.right+20 < qr.left && qr.bottom+20 < footer.top;
    }''')
    page.screenshot(path=str(QA / 'cover-qr-placeholder.png'))

    # Explicit public link, as used when a presenter runs the deck locally.
    destination = 'https://example.org/informs-tutorial/'
    html = (ROOT / '_site/index.html').read_text().replace('data-share-url=""', f'data-share-url="{destination}"', 1)
    page.route(url + 'index.html', lambda route: route.fulfill(body=html, content_type='text/html'))
    page.goto(url + 'index.html')
    page.wait_for_selector('[data-share-state="ready"]')
    assert page.locator('[data-share-link]').get_attribute('href') == destination
    qr_image = Image.open(BytesIO(page.locator('.cover-share img').screenshot()))
    decoded = zxingcpp.read_barcode(qr_image)
    assert decoded and decoded.text == destination
    page.screenshot(path=str(QA / 'cover-qr-live-example.png'))
    page.unroute(url + 'index.html')

    # Simulate a public repository URL with all requests fulfilled from local files.
    # This verifies automatic URL selection without publishing or visiting a site.
    public_base = 'https://slides.example.org/tutorial/'
    hosted = page.context.browser.new_page(viewport={'width':1440, 'height':900})

    def serve_fixture(route: Any) -> None:
        """Serve a simulated public deployment from the already rendered files."""
        relative = unquote(urlparse(route.request.url).path.removeprefix('/tutorial/')) or 'index.html'
        asset = ROOT / '_site' / relative
        route.fulfill(body=asset.read_bytes(), content_type=mimetypes.guess_type(asset)[0] or 'application/octet-stream')

    hosted.route(public_base + '**', serve_fixture)
    hosted.goto(public_base + 'index.html?presenter=1#/s03')
    hosted.wait_for_selector('[data-share-state="ready"]', state='attached')
    assert hosted.locator('[data-share-link]').get_attribute('href') == public_base + 'index.html'
    hosted.evaluate('Reveal.slide(0)')
    decoded = zxingcpp.read_barcode(Image.open(BytesIO(hosted.locator('.cover-share img').screenshot())))
    assert decoded and decoded.text == public_base + 'index.html'
    hosted.close()
    page.goto(url)
    page.wait_for_function('window.CONTENTS_READY && window.TUTORIAL_READY && Reveal.isReady()')


def go(page: Page, slide: int) -> None:
    """Navigate to a slide and wait for its transition to finish."""
    page.evaluate("i => Reveal.slide(i)", slide - 1)
    page.wait_for_timeout(350)


def check_interactions(page: Page) -> None:
    """Exercise decisions, state locking, reset, feasibility, and numerical controls."""
    go(page, 3)
    page.evaluate('Reveal.slide(2, 0, 1)')
    page.evaluate('''() => {
      window.originalDemandSampler=TutorialModels.sampleInventoryDemand;
      window.demandDraws=[];
      TutorialModels.sampleInventoryDemand=period=>{
        demandDraws.push(period);
        return [5,3,3,1][demandDraws.length-1];
      };
    }''')
    root = page.locator('[data-widget="inventory"]')
    first = root.locator('[data-input="order"]')
    assert 'Start with 0 in stock' in root.locator('.decision-event').first.inner_text()
    first.fill('6')
    next_order = root.locator('[data-input="next-order"]')
    advance = root.locator('[data-action="advance"]')
    assert root.locator('.inventory-outcome').count() == 0
    assert not next_order.is_visible()
    advance.click()
    assert first.is_disabled()
    assert page.evaluate('demandDraws.length') == 0
    assert root.locator('.inventory-outcome').count() == 0
    advance.click()
    assert page.evaluate('demandDraws.join()') == '0'
    assert '1 unit left in stock' in root.locator('.inventory-outcome').inner_text()
    assert 'Holding cost: $1' in root.locator('.inventory-outcome').inner_text()
    assert not next_order.is_disabled()
    assert 'Carry forward: 1 in stock' in root.locator('.decision-event').nth(2).inner_text()
    advance.click()
    assert next_order.is_disabled()
    assert page.evaluate('demandDraws.length') == 1
    advance.click()
    assert page.evaluate('demandDraws.join()') == '0,1'
    assert '1 unit of unmet demand' in root.locator('.inventory-outcome').nth(1).inner_text()
    assert 'Stockout cost: $25' in root.locator('.inventory-outcome').nth(1).inner_text()
    assert 'Total $166' in root.locator('.inventory-ledger').inner_text()
    page.wait_for_timeout(650)
    page.screenshot(path=str(QA / 'inventory-both-outcomes.png'))
    assert page.evaluate('document.querySelector("#s03 .slide-body").getBoundingClientRect().bottom < (document.querySelector("#s03 .source") || document.querySelector(".projected-footer")).getBoundingClientRect().top - 4'), 'Completed inventory timeline overlaps its source/footer'
    root.locator('[data-action="replay"]').click()
    first.fill('0')
    assert first.input_value() == '0'
    assert not first.is_disabled()
    assert root.locator('.inventory-outcome').count() == 0
    advance.click()
    advance.click()
    assert 'Stockout cost: $125' in root.locator('.inventory-outcome').inner_text()
    assert 'Carry forward: 5 unmet' in root.locator('.decision-event').nth(2).inner_text()
    page.wait_for_timeout(650)
    page.screenshot(path=str(QA / 'inventory-first-stockout.png'))
    advance.click()
    advance.click()
    assert 'Total $320' in root.locator('.inventory-ledger').inner_text()
    assert page.evaluate('demandDraws.length') == 2
    root.locator('[data-action="reset"]').click()
    assert not first.is_disabled()
    assert first.input_value() == '2'
    assert root.locator('.inventory-outcome').count() == 0
    for _ in range(4):
        advance.click()
    assert page.evaluate('demandDraws.join()') == '0,1,0,1'
    assert 'Total $110' in root.locator('.inventory-ledger').inner_text()
    assert 'Start with 0 in stock' in root.locator('.decision-event').first.inner_text()
    root.locator('[data-action="reset"]').click()
    page.evaluate('TutorialModels.sampleInventoryDemand=originalDemandSampler')
    go(page, 7)
    scale = page.locator('[data-widget="scale"]')
    scale.locator('input').fill('10')
    assert scale.locator('.big-number').first.get_attribute('data-count') == str(15**10)
    scale.locator('input').fill('30')
    assert scale.locator('.big-number').first.get_attribute('data-count') == str(15**30)
    assert scale.locator('.big-number').nth(1).get_attribute('data-count') == str(4**30)
    assert scale.locator('.big-number').evaluate_all('(els) => els.every(el => el.scrollWidth <= el.clientWidth + 1)')
    page.screenshot(path=str(QA / 'slide-07-large-counts.png'))
    scale.locator('[data-action="reset"]').click()
    assert scale.locator('input').input_value() == '1'
    assert scale.locator('.big-number').first.get_attribute('data-count') == '15'
    assert scale.locator('.big-number').nth(1).get_attribute('data-count') == '4'
    go(page, 8)
    methods = page.locator('[data-widget="methods"]')
    assert methods.locator('.method-detail:visible').count() == 1
    for family in ['dynamic', 'value', 'policy', 'tree', 'optimization', 'structure']:
        choice = methods.locator(f'[data-method="{family}"]')
        choice.click()
        assert choice.get_attribute('aria-pressed') == 'true'
        assert methods.locator('[aria-pressed="true"]').count() == 1
        panel = methods.locator(f'#method-panel-{family}')
        assert panel.is_visible()
        assert methods.locator('.method-detail:visible').count() == 1
        assert panel.locator('a[href^="https://"][target="_blank"][data-citation]').count() >= 1
        assert methods.evaluate('(el) => el.getBoundingClientRect().bottom < document.querySelector(".projected-footer").getBoundingClientRect().top - 4')
        page.screenshot(path=str(QA / f'slide-08-method-{family}.png'))
    methods.locator('[data-action="reset"]').click()
    assert methods.locator('#method-panel-optimization').is_visible()
    methods.locator('[data-method="optimization"]').focus()
    page.keyboard.press('Enter')
    assert methods.locator('#method-panel-optimization').is_visible()
    assert page.evaluate('Reveal.getIndices().h') == 7
    methods.locator('[data-action="reset"]').click()


def cor_fit_error(page: Page) -> float:
    """Measure the visible curve's squared distance from the fixed reference."""
    return page.locator('#s10 .cor-optimize .cor-sketch').evaluate('''svg => {
        const reference=svg.querySelector('.cor-piecewise'), curve=svg.querySelector('.cor-fit');
        const yAt=(path,x)=>{
            let lo=0,hi=path.getTotalLength();
            for(let i=0;i<22;i++){
                const mid=(lo+hi)/2;
                if(path.getPointAtLength(mid).x<x)lo=mid;else hi=mid;
            }
            return path.getPointAtLength((lo+hi)/2).y;
        };
        let error=0,count=0;
        for(let x=45;x<290;x+=8){error+=(yAt(curve,x)-yAt(reference,x))**2;count++;}
        return error/count;
    }''')


def check_navigation(page: Page) -> None:
    """Check visible navigation, fragments, button focus, and field focus escape."""
    go(page, 1)
    next_slide = page.locator('.controls .navigate-right')
    assert next_slide.is_visible()
    next_slide.click()
    page.wait_for_function('Reveal.getIndices().h === 1')
    next_slide.click()
    page.wait_for_function('document.querySelector("#s02 .fragment").classList.contains("visible")')
    next_slide.click()
    page.wait_for_function('Reveal.getIndices().h === 2')
    introduction = page.locator('#s03 .inventory-example-intro')
    animation = page.locator('#s03 [data-widget="inventory"]')
    assert not introduction.is_visible() and not animation.is_visible()
    next_slide.click()
    page.wait_for_function('document.querySelector("#s03 .inventory-example-intro").classList.contains("visible")')
    introduction.wait_for(state='visible')
    assert introduction.is_visible() and not animation.is_visible()
    assert page.evaluate('Reveal.getIndices().h') == 2
    next_slide.click()
    page.wait_for_function('document.querySelector("#s03 [data-widget=inventory]").classList.contains("visible")')
    animation.wait_for(state='visible')
    assert animation.is_visible()
    assert page.evaluate('Reveal.getIndices().h') == 2
    page.locator('[data-widget="inventory"] [data-action="reset"]').click()
    page.keyboard.press('Space')
    assert page.evaluate('Reveal.getIndices().h') == 2
    page.keyboard.press('ArrowRight')
    page.wait_for_function('Reveal.getIndices().h === 3')
    assert page.locator('#s04 tbody tr').first.is_visible()
    assert not page.locator('#s04 tbody tr').nth(1).is_visible()
    for step in range(6):
        page.keyboard.press('ArrowRight')
        page.wait_for_function('n => document.querySelectorAll("#s04 .fragment.visible").length === n', arg=step+1)
        assert page.evaluate('Reveal.getIndices().h') == 3
    page.wait_for_timeout(350)
    page.screenshot(path=str(QA / 'slide-04-terminology.png'))
    page.keyboard.press('ArrowLeft')
    page.wait_for_function('document.querySelectorAll("#s04 .fragment.visible").length === 5')
    page.keyboard.press('ArrowRight')
    page.wait_for_function('document.querySelectorAll("#s04 .fragment.visible").length === 6')
    page.keyboard.press('ArrowRight')
    page.wait_for_function('Reveal.getIndices().h === 4')
    for step in range(3):
        page.keyboard.press('ArrowRight')
        page.wait_for_function('n => document.querySelectorAll("#s05 .fragment.visible").length === n', arg=step+1)
        assert page.evaluate('Reveal.getIndices().h') == 4
    page.wait_for_timeout(350)
    page.screenshot(path=str(QA / 'slide-05-mdp.png'))
    page.keyboard.press('ArrowRight')
    page.wait_for_function('Reveal.getIndices().h === 5')
    for step in range(6):
        page.keyboard.press('ArrowRight')
        page.wait_for_function('n => document.querySelectorAll("#s06 .fragment.visible").length === n', arg=[1, 3, 5, 7, 9, 10][step])
        assert page.locator('#s06 .bellman-annotation.visible').count() == min(step, 4)
        assert page.evaluate('Reveal.getIndices().h') == 5
    page.wait_for_timeout(350)
    page.screenshot(path=str(QA / 'slide-06-bellman.png'))
    page.keyboard.press('ArrowRight')
    page.wait_for_function('Reveal.getIndices().h === 6')
    field = page.locator('[data-widget="scale"] input')
    field.focus()
    page.keyboard.press('ArrowRight')
    assert field.input_value() == '2'
    assert page.evaluate('Reveal.getIndices().h') == 6
    page.keyboard.press('Escape')
    page.keyboard.press('ArrowRight')
    page.wait_for_function('Reveal.getIndices().h === 7')
    next_slide.click()
    page.wait_for_function('Reveal.getIndices().h === 8')
    assert page.locator('#s09 .motivation-question').is_visible()
    assert page.locator('#s09 .fragment.visible').count() == 0
    for visible_count in [1, 2, 3, 5, 7, 8]:
        next_slide.click()
        page.wait_for_function('n => document.querySelectorAll("#s09 .fragment.visible").length === n', arg=visible_count)
        assert page.evaluate('Reveal.getIndices().h') == 8
    page.wait_for_timeout(350)
    assert page.locator('#s09 .motivation-workflow img').count() == 5
    assert page.locator('#s09 .motivation-workflow img').evaluate_all('(imgs) => imgs.every(img => img.complete && img.naturalWidth > 0)')
    page.screenshot(path=str(QA / 'slide-09-motivation.png'))
    next_slide.click()
    page.wait_for_function('Reveal.getIndices().h === 9')
    assert page.locator('#s10 .cor-stage:visible').count() == 1
    assert page.locator('#s10 .cor-artifact:visible').count() == 0
    page.screenshot(path=str(QA / 'slide-10-cor-start.png'))
    for step, visible_count in enumerate([1, 3, 4, 6, 7, 9]):
        next_slide.click()
        page.wait_for_function('n => document.querySelectorAll("#s10 .fragment.visible").length === n', arg=visible_count)
        assert page.evaluate('Reveal.getIndices().h') == 9
        page.locator('#s10 .cor-artifact').nth(min(step // 2, 2)).wait_for(state='visible')
        assert page.locator('#s10 .cor-artifact:visible').count() == min(step // 2 + 1, 3)
        if step == 0:
            # Inspect fixed animation times so load/screenshot latency cannot
            # turn a reference-before-approximation check into a timing race.
            for replay in [False, True]:
                if replay:
                    page.keyboard.press('ArrowLeft')
                    page.locator('#s10 .cor-artifact.cor-construct').wait_for(state='hidden')
                    page.wait_for_timeout(400)
                    page.keyboard.press('ArrowRight')
                page.wait_for_function('''() => document.querySelector('#s10 .cor-artifact.cor-construct')
                    .getAnimations({subtree:true}).some(a => a.effect.target.classList.contains('cor-representation'))''')
                page.evaluate('''() => {
                    window.corConstructAnimations = document.querySelector('#s10 .cor-artifact.cor-construct').getAnimations({subtree:true});
                    corConstructAnimations.forEach(a => {a.pause(); a.currentTime = 900;});
                }''')
                assert page.locator('#s10 .cor-sample').count() == 0
                assert page.locator('#s10 .cor-reference-reveal').evaluate('(p) => getComputedStyle(p).strokeDashoffset') == '0px'
                assert page.locator('#s10 .cor-representation').evaluate('(p) => getComputedStyle(p).strokeDashoffset') == '1px'
                if not replay:
                    page.screenshot(path=str(QA / 'slide-10-cor-piecewise.png'))
                    page.evaluate('corConstructAnimations.forEach(a => {a.currentTime = 1800;})')
                    progress = page.locator('#s10 .cor-representation').evaluate('(p) => parseFloat(getComputedStyle(p).strokeDashoffset)')
                    assert 0 < progress < 1
                    page.screenshot(path=str(QA / 'slide-10-cor-curve-drawing.png'))
                page.evaluate('corConstructAnimations.forEach(a => a.finish())')
                page.wait_for_function('getComputedStyle(document.querySelector("#s10 .cor-representation")).strokeDashoffset === "0px"')
        if step == 2:
            curve = page.locator('#s10 .cor-fit')
            reference = page.locator('#s10 .cor-optimize .cor-piecewise').get_attribute('d')
            assert page.locator('#s10 .cor-piecewise').evaluate_all('(paths) => paths.every(p => p.getAttribute("d") === paths[0].getAttribute("d"))')
            assert curve.evaluate('(p) => getComputedStyle(p).strokeDasharray') == 'none'
            initial_error = cor_fit_error(page)
            page.screenshot(path=str(QA / 'slide-10-cor-fit-initial.png'))
            # The whole curve is present while its shape changes, rather than
            # being progressively revealed as in Construct.
            page.wait_for_function('document.querySelector("#s10 .cor-fit").getPointAtLength(0).y > 32')
            middle_error = cor_fit_error(page)
            assert middle_error < initial_error
            page.screenshot(path=str(QA / 'slide-10-cor-fit-adjusting.png'))
            page.wait_for_function('document.querySelector("#s10 .cor-fit").getAttribute("d") === document.querySelector("#s10 .cor-previous-curve").getAttribute("d")')
            assert cor_fit_error(page) < min(middle_error, initial_error * .35)
            assert page.locator('#s10 .cor-optimize .cor-piecewise').get_attribute('d') == reference
            page.keyboard.press('ArrowLeft')
            page.locator('#s10 .cor-artifact.cor-optimize').wait_for(state='hidden')
            page.wait_for_function('document.querySelector("#s10 .cor-fit").getAttribute("d") === document.querySelector("#s10 .cor-fit").dataset.fitStart')
            page.keyboard.press('ArrowRight')
            page.wait_for_function('document.querySelector("#s10 .cor-fit").getAttribute("d") === document.querySelector("#s10 .cor-previous-curve").getAttribute("d")')
        if step in [0, 2, 4]:
            page.wait_for_timeout(850)
            page.screenshot(path=str(QA / f'slide-10-cor-step-{step+1}.png'))
    page.wait_for_timeout(1200)
    assert page.locator('#s10 .cor-feedback .cor-trace').evaluate('(el) => getComputedStyle(el).strokeDashoffset') == '0px'
    assert page.locator('#s10 .cor-artifact').evaluate_all('(cards) => cards.every(card => card.querySelector(".cor-caption").getBoundingClientRect().bottom <= card.getBoundingClientRect().bottom - 10)')
    page.screenshot(path=str(QA / 'slide-10-cor-complete.png'))
    page.keyboard.press('ArrowLeft')
    page.wait_for_function('document.querySelectorAll("#s10 .fragment.visible").length === 7')
    page.locator('#s10 .cor-feedback').wait_for(state='hidden')
    assert page.locator('#s10 .cor-feedback').is_hidden()
    assert page.locator('#s10 .cor-artifact:visible').count() == 3
    page.emulate_media(reduced_motion='reduce')
    next_slide.click()
    page.wait_for_function('document.querySelectorAll("#s10 .fragment.visible").length === 9')
    assert page.locator('#s10 .cor-feedback .cor-trace').evaluate('(el) => getComputedStyle(el).transitionDuration') == '0s'
    assert page.locator('#s10 .cor-feedback .cor-trace').evaluate('(el) => getComputedStyle(el).strokeDashoffset') == '0px'
    page.evaluate('Reveal.slide(9, 0, -1); Reveal.nextFragment();')
    assert page.locator('#s10 .cor-reference-reveal').evaluate('(p) => getComputedStyle(p).strokeDashoffset') == '0px'
    assert page.locator('#s10 .cor-representation').evaluate('(p) => getComputedStyle(p).strokeDashoffset') == '0px'
    page.evaluate('Reveal.slide(9, 0, 5)')
    page.wait_for_function('document.querySelector("#s10 .cor-fit").getAttribute("d") === document.querySelector("#s10 .cor-previous-curve").getAttribute("d")')
    page.emulate_media(reduced_motion='no-preference')
    next_slide.click()
    page.wait_for_function('Reveal.getIndices().h === 10')
    stages = [text.strip() for text in page.locator('#s11 .setting-stage dt').all_text_contents()]
    assert stages == ['Construct', 'Solve', 'Refine'] * 2
    assert [text.strip() for text in page.locator('#s11 .setting-solve dd').all_text_contents()] == ['Mathematical programming', 'First-order methods']
    assert page.locator('#s11 .setting-discrete').is_visible()
    assert page.locator('#s11 .setting-continuous').is_hidden()
    page.screenshot(path=str(QA / 'slide-11-discrete.png'))
    next_slide.click()
    page.locator('#s11 .setting-continuous').wait_for(state='visible')
    assert page.evaluate('Reveal.getIndices().h') == 10
    page.wait_for_timeout(350)
    page.screenshot(path=str(QA / 'slide-11-both-settings.png'))
    page.keyboard.press('ArrowLeft')
    page.locator('#s11 .setting-continuous').wait_for(state='hidden')
    assert page.locator('#s11 .setting-discrete').is_visible()
    page.keyboard.press('ArrowRight')
    page.locator('#s11 .setting-continuous').wait_for(state='visible')
    page.keyboard.press('ArrowRight')
    assert page.evaluate('Reveal.getIndices().h') == 11
    assert not page.evaluate('Reveal.isLastSlide()')


def check_assortment(page: Page) -> None:
    """Check the knapsack budget, prepared pricing, and weighted policy sampling."""
    page.wait_for_function('window.ASSORTMENT_READY')
    go(page, 12)
    assert page.locator('#s12 .assort-timeline').is_visible()
    root = page.locator('#s12 [data-assortment-widget]')
    root.locator('[data-product="2"]').click()
    assert 'exceeds budget' in root.locator('[data-selection-status]').inner_text()
    root.locator('[data-selection-reset]').click()
    assert '5 of 8 units used · feasible' == root.locator('[data-selection-status]').inner_text()
    root.locator('[data-product="0"]').focus()
    page.keyboard.press('Enter')
    assert '3 of 8 units' in root.locator('[data-selection-status]').inner_text()
    root.locator('[data-selection-reset]').click()
    root.locator('[data-product="1"]').click()
    root.locator('[data-product="2"]').click()
    assert '8 of 8 units used · feasible' == root.locator('[data-selection-status]').inner_text()
    root.locator('[data-product="0"]').click()
    root.locator('[data-product="1"]').click()
    assert '9 of 8 units used · exceeds budget' == root.locator('[data-selection-status]').inner_text()
    root.locator('[data-selection-reset]').click()
    go(page, 18)
    page.evaluate('Reveal.slide(17, 0, 1)')
    page.evaluate('window.savedPolicyRandom = Math.random; Math.random = () => 0.749999')
    page.locator('#s18 [data-policy-draw]').click()
    assert page.locator('#s18 [data-policy-choice]').inner_text() == 'Selected: backpack + cooler'
    page.evaluate('Math.random = () => 0.75')
    page.locator('#s18 [data-policy-draw]').click()
    assert page.locator('#s18 [data-policy-choice]').inner_text() == 'Selected: tent'
    page.evaluate('Math.random = window.savedPolicyRandom; delete window.savedPolicyRandom')
    page.locator('#s18 [data-policy-reset]').click()
    assert page.locator('#s18 [data-policy-choice]').inner_text() == 'Ready to sample'
    trace = page.evaluate('ASSORTMENT_DATA.trace')
    assert [row['objective'] for row in trace] == [31.5, 40]
    assert [row['policy_value'] for row in trace] == [26.5, 34]
    assert trace[0]['additions'] == [
        {'period': 0, 'action': [1, 0, 1], 'score': 7.5},
        {'period': 1, 'action': [1, 0, 1], 'score': 5}]
    assert not trace[-1]['additions']
    assert all(max(row['scores']) <= 1e-7 for row in trace[-1]['pricing'])
    assert page.locator('#s13 math').count() > 0
    assert page.locator('#s17 math').count() == 4
    for slide in range(12, 23):
        page.evaluate('i => Reveal.slide(i, 0, -1)', slide - 1)
        page.wait_for_timeout(350)
        steps = page.locator(f'#s{slide} .fragment').evaluate_all('(els) => new Set(els.map(e => e.dataset.fragmentIndex)).size')
        for _ in range(steps):
            page.keyboard.press('ArrowRight')
        assert page.evaluate('Reveal.getIndices().h') == slide - 1
        assert page.locator(f'#s{slide} .fragment:not(.visible)').count() == 0


def capture_deck(page: Page, count: int, prefix: str) -> list[dict[str, Any]]:
    """Capture every slide and check main content against footer and slide bounds."""
    assert page.evaluate('Reveal.getTotalSlides()') == count
    issues = []
    for i in range(count):
        go(page, i + 1)
        if prefix == 'slide' and i >= 11:
            page.evaluate('i => Reveal.slide(i, 0, 99)', i)
            page.wait_for_timeout(350)
        page.screenshot(path=str(QA / f'{prefix}-{i+1:02}.png'))
        issue = page.evaluate("""() => {
          const section=document.querySelector('section.present');
          const body=section.querySelector('.slide-body').getBoundingClientRect();
          const footer=document.querySelector('.projected-footer').getBoundingClientRect();
          const source=section.querySelector('.source')?.getBoundingClientRect() || footer;
          return {title:section.querySelector('h2').textContent,bodyBottom:body.bottom,
            sourceTop:source.top,footerTop:footer.top,overlap:body.bottom>source.top-4,
            horizontal:body.right>innerWidth-15};
        }""")
        if issue['overlap'] or issue['horizontal']:
            issues.append(issue)
    return issues


def check_python_lab(page: Page) -> None:
    """Run real browser SciPy solves, edit costs, recover errors, and stop a loop."""
    go(page, 23)
    page.wait_for_function('window.PYTHON_LAB_READY')
    root = page.locator('[data-python-lab]')
    editor = root.locator('textarea')
    original = editor.input_value()
    status = root.locator('[data-python-status]')

    def solve(code: str, objective: str) -> None:
        """Execute code and require the expected objective from the actual worker."""
        editor.fill(code)
        root.locator('[data-python-run]').click()
        page.wait_for_function('document.querySelector("[data-python-lab]").getAttribute("aria-busy") === "false"', timeout=90000)
        assert 'Optimal' in status.inner_text(), root.inner_text()
        assert root.locator('.python-objective').inner_text() == objective

    solve(original, '$40.00')
    assert '$34.00' in root.locator('.python-policy').inner_text()
    page.screenshot(path=str(QA / 'python-default.png'))
    solve(original.replace('True', 'False'), '$31.50')
    assert '$26.50' in root.locator('.python-policy').inner_text()
    solve(original.replace('[0, 0, 0]', '[0, 0, 25]'), '$28.00')
    assert root.locator('.python-weight').count() == 2
    assert root.locator('.python-weight span').all_text_contents() == ['Backpack + cooler'] * 2
    page.screenshot(path=str(QA / 'python-edited-costs.png'))
    editor.fill(original.replace('[0, 0, 0]', '[-1, 0, 0]'))
    root.locator('[data-python-run]').click()
    page.wait_for_function('document.querySelector("[data-python-lab]").getAttribute("aria-busy") === "false"')
    assert 'nonnegative costs' in root.locator('.python-error').inner_text()
    solve(original, '$40.00')
    editor.fill('while True:\n    pass')
    root.locator('[data-python-run]').click()
    root.locator('[data-python-stop]').click()
    assert 'Stopped' in status.inner_text()
    root.locator('[data-python-reset]').click()
    assert editor.input_value() == original
    assert root.locator('.python-objective').count() == 0
    editor.focus()
    page.keyboard.press('ArrowRight')
    assert page.evaluate('Reveal.getIndices().h') == 22
    page.keyboard.press('Escape')
    page.keyboard.press('ArrowRight')
    assert page.evaluate('Reveal.getIndices().h') == 23
    go(page, 23)
    solve(original, '$40.00')


def check_continuous(page: Page) -> None:
    """Check migrated notes, staged narration, readable bounds, and editable demos."""
    page.wait_for_function('window.MATH_POLISH_READY')
    assert page.locator('[data-math-error]').count() == 0
    assert page.locator('section[data-math-ready="true"]').count() == 19
    assert page.locator('[data-mjx-error]').count() == 0
    assert page.locator('.polished-math').evaluate_all(
        '(equations) => equations.every(e => (e.closest("section").id === "vfa-adaptation-transition" || Number(e.closest("section").id.slice(1)) >= 24))')
    imported = page.locator('.continuous-import-slide')
    assert imported.count() == MAIN_SLIDES - CONTINUOUS_START + 1
    assert imported.locator('.notes').count() == 18
    assert imported.locator('.notes').evaluate_all(
        '(notes) => notes.every(note => note.textContent.trim().length > 50)')
    demos = imported.locator('[data-continuous-python]')
    assert demos.count() == CONTINUOUS_DEMOS
    demo_ids = demos.evaluate_all('(labs) => labs.map(lab => lab.dataset.demoId)')
    assert len(set(demo_ids)) == CONTINUOUS_DEMOS
    for demo in demos.all():
        assert demo.locator('[data-demo-editor]').count() == 1
        assert demo.locator('[data-demo-editor]').input_value().strip()
        assert demo.locator('[data-demo-editor]').get_attribute('aria-label')
        for control in ('run', 'stop', 'reset'):
            assert demo.locator(f'[data-demo-{control}]').count() == 1
        assert demo.locator('[data-demo-status]').count() == 1
        assert demo.locator('[data-demo-output][aria-live="polite"]').count() == 1

    # Slide 24 introduces continuous quantities through three illustrated stages.
    # Check its reveals and every imported slide using next/previous controls.
    for slide in range(24, MAIN_SLIDES + 1):
        page.evaluate('i => Reveal.slide(i, 0, -1)', slide - 1)
        page.wait_for_timeout(100)
        section = page.locator('section.present')
        fragments = section.locator('.fragment')
        groups = fragments.evaluate_all(
            '(els) => [...new Set(els.map(e => Number(e.dataset.fragmentIndex)))].sort((a,b) => a-b)')
        assert groups, f'Slide {slide} has no staged reveal'
        assert section.locator('.fragment.visible').count() == 0
        for group in groups:
            expected = fragments.evaluate_all(
                '(els, index) => els.filter(e => Number(e.dataset.fragmentIndex) <= index).length', group)
            page.keyboard.press('ArrowRight')
            page.wait_for_function(
                '([id, count]) => document.querySelectorAll(`#${id} .fragment.visible`).length === count',
                arg=[f's{slide}', expected])
            assert page.evaluate('Reveal.getIndices().h') == slide - 1
        assert section.locator('.fragment:not(.visible)').count() == 0
        page.keyboard.press('ArrowLeft')
        page.wait_for_function(
            'id => document.querySelectorAll(`#${id} .fragment:not(.visible)`).length > 0',
            arg=f's{slide}')
        assert page.evaluate('Reveal.getIndices().h') == slide - 1
        page.keyboard.press('ArrowRight')
        page.wait_for_function(
            'id => document.querySelectorAll(`#${id} .fragment:not(.visible)`).length === 0',
            arg=f's{slide}')
        page.wait_for_timeout(350)
        bounds = section.locator('.slide-body').evaluate("""body => {
            const box=body.getBoundingClientRect();
            const footer=document.querySelector('.projected-footer').getBoundingClientRect();
            return {bottom:box.bottom, footerTop:footer.top, left:box.left,
                right:box.right, viewport:innerWidth, scrollWidth:body.scrollWidth,
                clientWidth:body.clientWidth};
        }""")
        assert bounds['bottom'] < bounds['footerTop'] - 4, (slide, bounds)
        assert bounds['left'] >= 0 and bounds['right'] <= bounds['viewport'], (slide, bounds)
        assert bounds['scrollWidth'] <= bounds['clientWidth'] + 1, (slide, bounds)

    # Editing code must retain arrow-key cursor movement without advancing the
    # presentation. Reset restores each demo's own original source.
    for demo_id in demo_ids:
        demo = page.locator(f'[data-demo-id="{demo_id}"]')
        slide = int(demo.evaluate('(lab) => lab.closest("section").id.slice(1)'))
        page.evaluate('i => Reveal.slide(i, 0, 99)', slide - 1)
        editor = demo.locator('[data-demo-editor]')
        original = editor.input_value()
        editor.fill(original + '\n# Participant edit')
        editor.focus()
        page.keyboard.press('ArrowRight')
        assert page.evaluate('Reveal.getIndices().h') == slide - 1
        page.keyboard.press('Escape')
        demo.locator('[data-demo-reset]').click()
        assert editor.input_value() == original


def contact_sheet(prefix: str, count: int) -> None:
    """Build compact screenshot sheets for visual inspection."""
    for start in range(0, count, 12):
        canvas = Image.new('RGB', (1440, 3 * 250), '#e8edf0')
        draw = ImageDraw.Draw(canvas)
        for j, n in enumerate(range(start + 1, min(start + 13, count + 1))):
            im = Image.open(QA / f'{prefix}-{n:02}.png')
            im.thumbnail((360, 225))
            x, y = (j % 4) * 360, (j // 4) * 250
            canvas.paste(im, (x, y + 22))
            draw.text((x + 12, y + 4), f'{prefix} {n}', fill='#182c3e')
        canvas.save(QA / f'{prefix}-sheet-{start//12+1}.png')


def main() -> None:
    """Run browser checks and write screenshots and layout diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', help='Check an existing preview URL instead of starting a static server.')
    args = parser.parse_args()
    QA.mkdir(exist_ok=True)
    server = None
    if args.url:
        url = args.url.rstrip('/') + '/'
    else:
        handler = functools.partial(QuietHandler, directory=str(ROOT.parent))
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}/presentation/_site/'
    errors, failed, external = [], [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: failed.append(r.url) if r.status >= 400 else None)
        page.on('request', lambda r: external.append(r.url) if not r.url.startswith(url) else None)
        page.goto(url)
        page.wait_for_function('window.TUTORIAL_READY && window.ASSORTMENT_READY && window.Reveal && window.Reveal.isReady()')
        assert page.locator('[data-error]').count() == 0
        assert page.locator('[data-widget]:not([data-ready])').count() == 0
        assert page.locator('.projected-footer img').count() == 3
        check_contents_and_sharing(page, url)
        check_models(page)
        check_navigation(page)
        check_assortment(page)
        check_python_lab(page)
        check_continuous(page)
        issues = capture_deck(page, MAIN_SLIDES, 'slide')
        check_interactions(page)
        page.goto(url + 'backup.html')
        page.wait_for_function('window.TUTORIAL_READY && window.Reveal && window.Reveal.isReady()')
        page.wait_for_function('window.CONTENTS_READY')
        assert page.locator('.slide-menu-item').count() == 11
        issues += capture_deck(page, 11, 'backup')
        print('Projected layout issues:', json.dumps(issues))
        for width in [1200, 390]:
            page.set_viewport_size({'width': width, 'height': 900})
            page.goto(url + 'reading.html')
            page.wait_for_function('window.TUTORIAL_READY && window.MATH_POLISH_READY')
            assert page.locator('main section.level2').count() == MAIN_SLIDES
            assert page.locator('#s10 .cor-stage:visible').count() == 3
            assert page.locator('#s10 .cor-artifact:visible').count() == 3
            assert page.locator('#s10 .cor-feedback').is_visible()
            assert page.locator('#s10 .cor-fit').get_attribute('d') == page.locator('#s10 .cor-previous-curve').get_attribute('d')
            assert page.locator('#s10 .cor-artifact').evaluate_all('(cards) => cards.every(card => card.querySelector(".cor-caption").getBoundingClientRect().bottom <= card.getBoundingClientRect().bottom - 10)')
            overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
            if overflow:
                print('Reading overflow at width', width, page.evaluate("""() => [...document.querySelectorAll('main *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,20).map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right,text:e.textContent.slice(0,70)}))"""))
            assert not overflow
            assert page.locator('[data-error]').count() == 0
            page.screenshot(path=str(QA / f'reading-{width}.png'))
            page.locator('#s10 .cor-flow').screenshot(path=str(QA / f'reading-cor-{width}.png'))
            assert [text.strip() for text in page.locator('#s11 .setting-stage dt').all_text_contents()] == ['Construct', 'Solve', 'Refine'] * 2
            assert page.locator('#s11 .setting-continuous').is_visible()
            page.locator('#s11 .slide-body').screenshot(path=str(QA / f'reading-settings-{width}.png'))
            for number in (12, 13, 16, 17, 18, 20, 21, 22, 23, 25, 27, 28, 31, 34, 36, 40, 41, 42):
                page.locator(f'#s{number} .slide-body').screenshot(path=str(QA / f'reading-assortment-{number}-{width}.png'))
        browser.close()
    if server:
        server.shutdown()
    contact_sheet('slide', MAIN_SLIDES)
    contact_sheet('backup', 11)
    report = {'errors': errors, 'failed_requests': failed, 'external_requests': external, 'layout_issues': issues}
    (QA / 'browser-results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    assert not errors and not failed and not external, report
    assert not issues, 'See layout_issues in qa/browser-results.json'
    print(f'PASS at {url}: {MAIN_SLIDES} main slides, 11 backups, navigation, interactions, local assets, and desktop/mobile reading views.')


if __name__ == '__main__':
    main()
