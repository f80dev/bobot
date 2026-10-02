import { Component, ChangeDetectionStrategy } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { RouterLink } from '@angular/router';

/**
 * History placeholder. Psybot is stateless (history lives in the browser
 * signal), so there is no server-side persistence to query. A future
 * enhancement could store turns in localStorage and surface them here.
 */
@Component({
  selector: 'app-history',
  imports: [MatCardModule, MatIconModule, MatButtonModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <mat-card class="history-card">
      <mat-card-header>
        <mat-card-title>Historique des conversations</mat-card-title>
      </mat-card-header>
      <mat-card-content>
        <div class="empty">
          <mat-icon class="empty-icon">history_toggle_off</mat-icon>
          <h3>Aucun historique persisté</h3>
          <p>
            Psybot est sans état : chaque conversation vit dans l'onglet courant
            du navigateur. Cette page est prévue pour afficher les sessions
            passées une fois la persistance activée (localStorage ou backend).
          </p>
          <a mat-flat-button color="primary" routerLink="/chat">
            <mat-icon>chat</mat-icon>
            Démarrer une conversation
          </a>
        </div>
      </mat-card-content>
    </mat-card>
  `,
  styles: [
    `
      .history-card {
        max-width: 720px;
        margin: 0 auto;
      }
      .empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 3rem 1rem;
        gap: 1rem;
      }
      .empty-icon {
        font-size: 48px;
        height: 48px;
        width: 48px;
        color: var(--mat-sys-on-surface-variant);
      }
    `,
  ],
})
export class History {}