import { Injectable } from '@nestjs/common';
import * as NodeCache from 'node-cache';

@Injectable()
export class AuthService {
  private readonly currentlyAuthenticated = new NodeCache({
    stdTTL: 600,
    checkperiod: 0,
  });

  isAuthenticated(accessToken: string): boolean {
    return this.currentlyAuthenticated.has(accessToken);
  }

  start(accessToken: string) {
    this.currentlyAuthenticated.set(accessToken, '');
  }
}
