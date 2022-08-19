import { AuthService } from './auth.service';
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { Request } from 'express';

@Injectable()
export class GoogleOAuthGuard extends AuthGuard('google') {
  constructor() {
    super({
      accessType: 'offline',
    });
  }
}

@Injectable()
export class IsUserAuthorized implements CanActivate {
  constructor(private readonly auth: AuthService) {}

  canActivate(context: ExecutionContext) {
    const req = context.switchToHttp().getRequest<Request>();
    const token = req.query['accessToken'];
    return typeof token === 'string' && this.auth.isAuthenticated(token);
  }
}
