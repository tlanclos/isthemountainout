import { REDIRECT_URL } from './config';
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { OAuth2Strategy, VerifyFunction } from 'passport-google-oauth';
import { AuthService } from './auth.service';

@Injectable()
export class GoogleAuthStrategy extends PassportStrategy(
  OAuth2Strategy,
  'google',
) {
  constructor(private readonly auth: AuthService) {
    super({
      clientID: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      callbackURL: REDIRECT_URL,
      scope: ['email', 'profile'],
    });
  }

  async validate(
    accessToken: string,
    refreshToken: string,
    profile: any,
    done: VerifyFunction,
  ): Promise<unknown> {
    const { name, emails, photos } = profile;
    const user: User = {
      email: emails[0].value,
      firstName: name.givenName,
      lastName: name.familyName,
      picture: photos[0].value,
      accessToken,
      refreshToken,
    };
    if (user) {
      this.auth.start(accessToken);
      done(null, user);
    } else {
      done(new UnauthorizedException(), null);
    }
    return;
  }
}

export interface User {
  readonly email: string;
  readonly firstName: string;
  readonly lastName: string;
  readonly picture: string;
  readonly accessToken: string;
  readonly refreshToken?: string;
}
