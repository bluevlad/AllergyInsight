import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://www.unmong.com:4040';

test.describe('Health Check API', () => {
  test('GET /api/health - 서버 상태 확인', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/health`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
  });
});

test.describe('Allergens API', () => {
  test('GET /api/allergens - 알러젠 목록 조회', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/allergens`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('food');
    expect(data).toHaveProperty('inhalant');
    expect(Array.isArray(data.food)).toBe(true);
  });

  test('알러젠 데이터 구조 확인', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/allergens`);
    const data = await response.json();
    const firstAllergen = data.food[0];
    expect(firstAllergen).toHaveProperty('code');
    expect(firstAllergen).toHaveProperty('name_kr');
    expect(firstAllergen).toHaveProperty('name_en');
  });
});

test.describe('Papers API', () => {
  test('GET /api/papers - 논문 목록 조회', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/papers`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(Array.isArray(data.items)).toBe(true);
  });

  test('GET /api/papers?query=allergy - 검색어로 논문 조회', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/papers?query=allergy`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('items');
  });

  test('GET /api/papers/1 - 개별 논문 조회', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/papers/1`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('title');
    expect(data).toHaveProperty('authors');
  });
});

test.describe('Search API', () => {
  test('POST /api/search - 논문 검색', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/search`, {
      data: { allergen: 'milk' }
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data).toHaveProperty('papers');
  });

  test('POST /api/search - allergen 없이 요청 시 에러', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/search`, {
      data: { query: 'allergy' }
    });
    expect(response.status()).toBe(422);
  });
});

test.describe('API 에러 처리', () => {
  test('존재하지 않는 엔드포인트', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/nonexistent`);
    expect(response.status()).toBe(404);
  });

  test('잘못된 HTTP 메서드', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/search`);
    expect(response.status()).toBe(405);
  });
});

test.describe('API 성능', () => {
  test('Health API 응답 시간', async ({ request }) => {
    const startTime = Date.now();
    await request.get(`${BASE_URL}/api/health`);
    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(2000);
  });
});

test.describe('페이지네이션', () => {
  test('Papers API 페이지네이션', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/papers?page=1&size=10`);
    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('page');
  });
});
