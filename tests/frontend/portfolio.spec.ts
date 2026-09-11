import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

async function mockLive(page: Page): Promise<void> {
  await page.route('**/api/coldfile', route => route.fulfill({ json: { episode_count: 15, latest: { video_id: 'dQw4w9WgXcQ', title: 'The mystery of the northern lights', published: '2026-09-10T12:00:00Z' } } }));
  await page.route('**/api/status', route => route.fulfill({ json: { checked_at: '2026-09-11T12:00:00Z', services: [{ id: 'site', name: 'gustavchristensen.dev', desc: 'Portfolio', url: 'https://gustavchristensen.dev', status: 'up', latency_ms: 12 }] } }));
  await page.route('**/api/github-activity', route => route.fulfill({ json: { username: 'Ajollyworld79', total: 693, weeks: Array.from({ length: 53 }, (_, index) => ({ contributionDays: index === 0 ? [{ date: '2026-09-10', contributionCount: 3, weekday: 4 }] : [] })) } }));
  await page.route('https://www.youtube-nocookie.com/**', route => route.fulfill({ contentType: 'text/html', body: '<p>Mock video</p>' }));
}

for (const width of [375, 768, 1024, 1440]) {
  test(`all pages render and fit at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    await mockLive(page);
    for (const [path, heading] of [['/', 'Gustav'], ['/about', 'Gustav Wind Christensen'], ['/projects', 'Projects']]) {
      await page.goto(path ?? '/');
      await expect(page.getByRole('heading', { level: 1 })).toContainText(heading ?? '');
      await expect(page.locator('nav [aria-current="page"]')).toHaveCount(1);
      await page.evaluate(() => document.fonts.ready);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await page.screenshot({ path: `test-results/${path?.replaceAll('/', '') || 'home'}-${width}.png`, fullPage: true });
    }
    expect(errors).toEqual([]);
  });
}

test('prerendered content and navigation work without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:8010/projects');
  await expect(page.getByRole('heading', { name: 'Projects' })).toBeVisible();
  await expect(page.locator('.project-card')).toHaveCount(6);
  await page.getByRole('link', { name: 'About', exact: true }).click();
  await expect(page.getByRole('heading', { name: /Experience/ })).toBeVisible();
  await context.close();
});

test('GitHub calendar accepts the backend format and preserves weekday positions', async ({ page }) => {
  await mockLive(page);
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /GitHub Activity/ })).toBeVisible();
  await expect(page.getByRole('img', { name: '693 GitHub contributions over the past year' })).toBeVisible();
  await expect(page.locator('.gh-cell')).toHaveAttribute('y', '70');
  await expect(page.locator('.stats-strip > div').last()).toContainText('650');
  await expect(page.locator('.gh-legend')).toContainText('More');
});

test('pages reflow with 200 percent text on a small phone', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 900 });
  await mockLive(page);
  for (const path of ['/', '/about', '/projects']) {
    await page.goto(path);
    await page.addStyleTag({ content: 'html{font-size:200% !important}' });
    await page.evaluate(() => document.fonts.ready);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
});

test('all Experience markers remain centred on the original timeline', async ({ page }) => {
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto('/about');
    await expect(page.locator('.timeline-item')).toHaveCount(8);
    const offsets = await page.locator('.timeline').evaluateAll(lists => lists.flatMap(list => {
      const line = getComputedStyle(list, '::before');
      const centre = list.getBoundingClientRect().x + parseFloat(line.left) + parseFloat(line.width) / 2;
      return [...list.children].map(item => {
        const marker = getComputedStyle(item, '::before');
        return item.getBoundingClientRect().x + parseFloat(marker.left) + parseFloat(marker.width) / 2 - centre;
      });
    }));
    expect(offsets.every(offset => Math.abs(offset) <= .5)).toBe(true);
  }
});

test('video mounts on demand, traps focus, closes and restores focus', async ({ page }) => {
  await mockLive(page); await page.goto('/');
  const play = page.getByRole('button', { name: 'Play episode: The mystery of the northern lights' });
  await expect(page.locator('iframe')).toHaveCount(0);
  await play.click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Close dialog' })).toBeFocused();
  await expect(page.locator('iframe')).toHaveAttribute('src', /youtube-nocookie\.com\/embed\/.+autoplay=1/);
  await page.keyboard.press('Shift+Tab');
  await expect(page.getByRole('dialog').getByRole('link', { name: 'Watch on YouTube' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.locator('iframe')).toHaveCount(0);
  await expect(play).toBeFocused();
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe('hidden');
  await play.click(); await page.mouse.click(2, 2); await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.setViewportSize({ width: 844, height: 390 });
  await play.click();
  const box = await page.getByRole('dialog').boundingBox();
  expect(box && box.y >= 0 && box.y + box.height <= 390).toBeTruthy();
  await page.getByRole('button', { name: 'Close dialog' }).click();
  await expect(page.locator('iframe')).toHaveCount(0);
});

test('projects expand, diagrams enlarge and apology demo opens', async ({ page }) => {
  await page.route('**/api/get-apology', route => route.fulfill({ json: { apology: 'Sorry for the tiny glitch.', meta: 'Generated via MCP' } }));
  await page.goto('/projects#data-pipeline');
  await page.locator('#data-pipeline summary').click();
  await expect(page.locator('#data-pipeline details')).toHaveAttribute('open', '');
  await page.getByRole('button', { name: /Enlarge architecture diagram: ETL/ }).click();
  await expect(page.locator('.dialog-diagram')).toBeVisible();
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Generate Live Apology' }).click();
  await expect(page.getByRole('dialog')).toContainText('Sorry for the tiny glitch.');
  await page.keyboard.press('Escape');
});

test('streamed chat renders safe markdown and sources', async ({ page }) => {
  await mockLive(page);
  await page.route('**/api/cv-chat-stream', route => route.fulfill({ contentType: 'text/event-stream', body: [
    { type: 'stage', stage: 'retrieve' }, { type: 'meta', source: 'rag', model: 'test-model', sources: [{ filename: 'cv.txt', score: .9, excerpt: 'Gustav builds Python systems.' }] },
    { type: 'token', t: '**Python** systems. <script>window.bad=true</script>' }, { type: 'done' },
  ].map(event => 'data: ' + JSON.stringify(event) + '\n\n').join('') }));
  await page.goto('/');
  await page.getByRole('button', { name: /What is Gustav's experience/ }).click();
  await expect(page.locator('.chat-message.assistant strong')).toHaveText('Python');
  await expect(page.getByRole('textbox', { name: 'Your question about Gustav' })).toBeFocused();
  await page.getByText('Answer sources', { exact: true }).click();
  await expect(page.locator('.chat-trace')).toContainText('cv.txt');
  expect(await page.evaluate(() => 'bad' in window)).toBe(false);
});

test('rate limits do not trigger a second request', async ({ page }) => {
  let fallbacks = 0;
  await mockLive(page);
  await page.route('**/api/cv-chat-stream', route => route.fulfill({ status: 429, json: { answer: 'Slow down.' } }));
  await page.route('**/api/cv-chat', route => { fallbacks++; return route.fulfill({ json: {} }); });
  await page.goto('/');
  await page.getByRole('button', { name: /What is Gustav's experience/ }).click();
  await expect(page.getByRole('alert')).toContainText('Too many questions');
  expect(fallbacks).toBe(0);
});

test('chat and live-data errors have usable fallbacks', async ({ page }) => {
  await page.route('**/api/**', route => route.fulfill({ status: 503, json: { error: 'offline' } }));
  await page.route('**/api/cv-chat', route => route.fulfill({ json: { answer: 'Gustav builds production systems.', source: 'mock' } }));
  await page.goto('/');
  await expect(page.getByText(/Live checks are temporarily unavailable/)).toBeVisible();
  await expect(page.getByText(/Latest episode unavailable/)).toBeVisible();
  await expect(page.getByText('GitHub activity is temporarily unavailable.', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: /What is Gustav's experience/ }).click();
  await expect(page.locator('.chat-message.assistant')).toContainText('Gustav builds production systems.');
  await expect(page.getByText('Using saved CV facts', { exact: true })).toBeVisible();
});
