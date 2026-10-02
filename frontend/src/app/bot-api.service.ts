import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ChatRequest,
  ChatResponse,
  HealthResponse,
} from './bot-api.types';

/**
 * Thin client for the bobot API. The default base URL targets the FastAPI
 * dev server on :8000. The Angular dev server proxies nothing — CORS is
 * handled by the backend (see bobot.py:_ALLOWED_ORIGINS).
 *
 * In production, set apiBase to the deployed bobot URL via environment.ts.
 */
@Injectable({ providedIn: 'root' })
export class BotApiService {
  private readonly http = inject(HttpClient);

  /** Override at runtime if you need to point at a deployed bot. */
  apiBase = '';

  private url(path: string): string {
    if (this.apiBase) {
      return `${this.apiBase}${path}`;
    }
    // Direct hit on the FastAPI server. The CORS middleware in bobot.py allows
    // http://localhost:4200, which is what the Angular dev server binds to.
    return `http://localhost:8000${path}`;
  }

  health(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(this.url('/api/health/psybot'));
  }

  chat(req: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(this.url('/api/psybot/chat'), req);
  }
}