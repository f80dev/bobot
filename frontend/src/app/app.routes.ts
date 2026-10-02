import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: '/chat',
  },
  {
    path: 'chat',
    loadComponent: () =>
      import('./pages/chat/chat').then((m) => m.Chat),
    title: 'bobot — Chat',
  },
  {
    path: 'history',
    loadComponent: () =>
      import('./pages/history/history').then((m) => m.History),
    title: 'bobot — Historique',
  },
  {
    path: 'admin',
    loadComponent: () =>
      import('./pages/admin/admin').then((m) => m.Admin),
    title: 'bobot — Admin',
  },
  {
    path: '**',
    redirectTo: '/chat',
  },
];