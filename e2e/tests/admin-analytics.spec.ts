import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://www.unmong.com:4040';

test.describe('Admin Analytics API - 인증 검증', () => {
  test('GET /api/admin/analytics/overview - 인증 없이 401/403 응답', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/admin/analytics/overview`);
    expect([401, 403]).toContain(response.status());
  });

  test('GET /api/admin/analytics/activity/stats - 인증 없이 401/403 응답', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/admin/analytics/activity/stats`);
    expect([401, 403]).toContain(response.status());
  });

  test('GET /api/admin/analytics/keywords/overview - 인증 없이 401/403 응답', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/admin/analytics/keywords/overview`);
    expect([401, 403]).toContain(response.status());
  });
});

test.describe('Admin Analytics 페이지 접근', () => {
  test('/admin/analytics 라우트 페이지 로드', async ({ page }) => {
    const startTime = Date.now();
    await page.goto(`${BASE_URL}/admin/analytics`, { waitUntil: 'networkidle', timeout: 10000 });
    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(10000);
  });
});
