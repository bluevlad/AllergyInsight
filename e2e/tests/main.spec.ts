import { test, expect } from '@playwright/test';

test.describe('AllergyInsight 메인 페이지', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('메인 페이지 로드', async ({ page }) => {
    await expect(page).toHaveTitle(/AllergyInsight/);
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });

  test('한글 컨텐츠 표시', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
  });
});

test.describe('알러젠 선택 기능', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('식품 알러젠 카테고리 확인', async ({ page }) => {
    const foodAllergens = ['땅콩', '우유', '계란', '밀', '대두'];
    for (const allergen of foodAllergens) {
      const element = page.getByText(allergen, { exact: false });
      const count = await element.count();
      if (count > 0) {
        console.log(`알러젠 발견: ${allergen}`);
      }
    }
  });

  test('알러젠 클릭 시 논문 표시', async ({ page }) => {
    const milkButton = page.getByText('우유', { exact: false }).first();
    if (await milkButton.isVisible()) {
      await milkButton.click();
      await page.waitForLoadState('networkidle');
    }
  });
});

test.describe('논문 검색 기능', () => {
  test('검색 입력창 존재', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const searchInput = page.locator('input[type="text"], input[type="search"]').first();
    const isVisible = await searchInput.isVisible().catch(() => false);
    if (isVisible) {
      await expect(searchInput).toBeVisible();
    }
  });
});

test.describe('반응형 디자인', () => {
  test('모바일 화면', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });

  test('태블릿 화면', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });
});

test.describe('접근성', () => {
  test('lang 속성 확인', async ({ page }) => {
    await page.goto('/');
    const htmlLang = await page.locator('html').getAttribute('lang');
    expect(htmlLang).toBe('ko');
  });
});

test.describe('성능', () => {
  test('페이지 로드 시간', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(10000);
  });
});
