import { AuthService } from './auth.service';
import { AuthController } from './auth.controller';
import { ConfigModule } from '@nestjs/config';
import { GoogleAuthStrategy } from './google-auth.strategy';
import { ClassificationsController } from './classifications.controller';
import { MountainController } from './mountain.controller';
import { join } from 'path';
import { Module } from '@nestjs/common';
import { ServeStaticModule } from '@nestjs/serve-static';
import { PassportModule } from '@nestjs/passport';

@Module({
  imports: [
    ServeStaticModule.forRoot({
      rootPath: join(__dirname, '../frontend/dist/frontend'),
    }),
    PassportModule.register({
      defaultStrategy: 'google',
    }),
    ConfigModule.forRoot({}),
  ],
  controllers: [AuthController, ClassificationsController, MountainController],
  providers: [GoogleAuthStrategy, AuthService],
})
export class AppModule {}
