import {
  Component,
  inject,
  signal,
  computed,
  effect,
  ChangeDetectionStrategy,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { BotApiService } from '../../bot-api.service';
import {
  ChatMessage,
  ChatResponse,
  SourceHit,
  TrajectoryStep,
} from '../../bot-api.types';

interface Turn {
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceHit[];
  emergency?: boolean;
  trajectory?: TrajectoryStep[];
  ts: number;
}

@Component({
  selector: 'app-chat',
  imports: [
    FormsModule,
    DatePipe,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatChipsModule,
    MatDividerModule,
    MatExpansionModule,
    MatSnackBarModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './chat.html',
  styleUrl: './chat.scss',
})
export class Chat {
  private readonly api = inject(BotApiService);
  private readonly snack = inject(MatSnackBar);

  protected readonly turns = signal<Turn[]>([]);
  protected readonly draft = signal('');
  protected readonly busy = signal(false);
  protected readonly sessionId = signal<string | null>(null);

  protected readonly canSend = computed(
    () => !this.busy() && this.draft().trim().length > 0 && this.draft().length <= 1500,
  );

  constructor() {
    // Auto-scroll to bottom on new turns.
    effect(() => {
      this.turns();
      queueMicrotask(() => {
        const el = document.querySelector('.chat-thread');
        if (el) el.scrollTop = el.scrollHeight;
      });
    });
  }

  protected onDraftChange(value: string): void {
    this.draft.set(value);
  }

  protected newSession(): void {
    this.turns.set([]);
    this.sessionId.set(this.makeUuid());
    this.snack.open('Nouvelle conversation', 'OK', { duration: 2000 });
  }

  protected async send(): Promise<void> {
    const text = this.draft().trim();
    if (!text || this.busy()) return;

    if (!this.sessionId()) this.sessionId.set(this.makeUuid());

    const userTurn: Turn = { role: 'user', content: text, ts: Date.now() };
    this.turns.update((t) => [...t, userTurn]);
    this.draft.set('');
    this.busy.set(true);

    const history: ChatMessage[] = this.turns()
      .filter((t) => !t.emergency)
      .slice(-6, -1)
      .map((t) => ({ role: t.role, content: t.content }));

    try {
      const resp: ChatResponse = await this.api
        .chat({ message: text, session_id: this.sessionId(), history })
        .toPromise();
      if (!resp) throw new Error('Réponse vide du serveur');
      const assistantTurn: Turn = {
        role: 'assistant',
        content: resp.answer,
        sources: resp.sources,
        emergency: resp.emergency,
        trajectory: resp.trajectory,
        ts: Date.now(),
      };
      this.turns.update((t) => [...t, assistantTurn]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erreur inconnue';
      this.snack.open(`Échec de l'appel bot: ${msg}`, 'Fermer', { duration: 5000 });
    } finally {
      this.busy.set(false);
    }
  }

  protected trackByIndex(index: number): number {
    return index;
  }

  protected asObjectKeys(o: Record<string, unknown>): string[] {
    return Object.keys(o);
  }

  private makeUuid(): string {
    // RFC 4122 v4 — non-identifying, session-scoped only.
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
      return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}