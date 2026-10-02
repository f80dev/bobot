import { Component, inject, signal, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { BotApiService } from '../../bot-api.service';
import { HealthResponse } from '../../bot-api.types';

/**
 * Admin / debug page — calls /api/health/psybot to surface the bot's runtime
 * configuration (mock vs real LLM, max iters, knowledge dir). Useful for
 * verifying wiring in dev without curling the FastAPI directly.
 */
@Component({
  selector: 'app-admin',
  imports: [
    DatePipe,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatDividerModule,
    MatSnackBarModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <mat-card class="admin-card">
      <mat-card-header>
        <mat-card-title>Admin / debug</mat-card-title>
        <mat-card-subtitle>
          État de l'API bobot au moment de la dernière interrogation
        </mat-card-subtitle>
        <div class="header-actions">
          <button mat-stroked-button (click)="refresh()" [disabled]="busy()">
            <mat-icon>refresh</mat-icon>
            Rafraîchir
          </button>
        </div>
      </mat-card-header>

      <mat-card-content>
        @if (busy() && !health()) {
          <div class="busy">
            <mat-spinner diameter="20" />
            <span>Appel de /api/health/psybot…</span>
          </div>
        }

        @if (error(); as err) {
          <p class="error">
            <mat-icon>error</mat-icon>
            {{ err }}
          </p>
        }

        @if (health(); as h) {
          <dl class="kv">
            <dt>Statut</dt>
            <dd>
              <mat-icon class="ok">check_circle</mat-icon>
              {{ h.status }}
            </dd>

            <dt>Mode LLM</dt>
            <dd>
              @if (h.llm_mock) {
                <mat-icon class="warn">bug_report</mat-icon> Mock (offline)
              } @else {
                <mat-icon class="ok">cloud_done</mat-icon> DeepSeek réel
              }
            </dd>

            <dt>Itérations max</dt>
            <dd>{{ h.max_iters }}</dd>

            <dt>Base de connaissances</dt>
            <dd><code>{{ h.knowledge_dir }}</code></dd>

            <dt>Dernière vérification</dt>
            <dd>{{ checkedAt() | date: 'medium' }}</dd>
          </dl>
          <mat-divider />
          <p class="hint">
            Pour itérer sur le serveur bobot : édite
            <code>~/bobot/bobot.py</code>, puis relance
            <code>python3 -m bobot</code> côté backend et
            <code>ng serve</code> côté frontend.
          </p>
        }
      </mat-card-content>
    </mat-card>
  `,
  styles: [
    `
      .admin-card {
        max-width: 720px;
        margin: 0 auto;
      }
      .header-actions {
        margin-left: auto;
      }
      .busy {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem;
      }
      .error {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #c0392b;
      }
      .kv {
        display: grid;
        grid-template-columns: 200px 1fr;
        gap: 0.5rem 1rem;
        margin: 1rem 0;
      }
      .kv dt {
        font-weight: 500;
        color: var(--mat-sys-on-surface-variant);
      }
      .kv dd {
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.25rem;
      }
      .ok {
        color: #2e7d32;
      }
      .warn {
        color: #ef6c00;
      }
      .hint {
        font-size: 0.85rem;
        color: var(--mat-sys-on-surface-variant);
        padding-top: 1rem;
      }
      code {
        font-family: monospace;
        background: var(--mat-sys-surface-container);
        padding: 0.1rem 0.3rem;
        border-radius: 4px;
      }
    `,
  ],
})
export class Admin implements OnInit {
  private readonly api = inject(BotApiService);
  private readonly snack = inject(MatSnackBar);

  protected readonly health = signal<HealthResponse | null>(null);
  protected readonly busy = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly checkedAt = signal<number>(0);

  ngOnInit(): void {
    this.refresh();
  }

  protected async refresh(): Promise<void> {
    this.busy.set(true);
    this.error.set(null);
    try {
      const h = await this.api.health().toPromise();
      if (!h) throw new Error('Réponse vide du serveur');
      this.health.set(h);
      this.checkedAt.set(Date.now());
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erreur inconnue';
      this.error.set(`Impossible de joindre l'API bobot : ${msg}`);
      this.health.set(null);
      this.snack.open('Health check échoué', 'Fermer', { duration: 4000 });
    } finally {
      this.busy.set(false);
    }
  }
}