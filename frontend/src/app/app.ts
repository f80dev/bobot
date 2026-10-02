import { Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatDividerModule,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly title = signal('bobot');
  protected readonly opened = signal(true);

  protected readonly nav: readonly NavItem[] = [
    { path: '/chat', label: 'Chat', icon: 'chat' },
    { path: '/history', label: 'Historique', icon: 'history' },
    { path: '/admin', label: 'Admin', icon: 'admin_panel_settings' },
  ];

  protected toggleNav(): void {
    this.opened.update((v) => !v);
  }
}