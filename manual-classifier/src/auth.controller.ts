import { User } from './google-auth.strategy';
import { GoogleOAuthGuard } from './google-auth.guard';
import { Controller, Get, UseGuards, Res, Req } from '@nestjs/common';
import { Request, Response } from 'express';

@Controller('auth')
export class AuthController {
  @Get()
  @UseGuards(GoogleOAuthGuard)
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  authenticate() {}

  @Get('validate')
  @UseGuards(GoogleOAuthGuard)
  async validate(@Req() req: Request, @Res() res: Response) {
    const user = req.user as User;
    const query = `accessToken=${encodeURIComponent(user.accessToken)}`;
    res.redirect(`/?${query}`);
  }
}
