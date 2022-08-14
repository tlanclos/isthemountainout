import { ClassificationsController } from './classifications.controller';
import { MountainController } from './mountain.controller';
import { join } from 'path';
import { Module } from '@nestjs/common';
import { ServeStaticModule } from '@nestjs/serve-static';

@Module({
  imports: [
    ServeStaticModule.forRoot({
      rootPath: join(__dirname, '../frontend/dist/frontend'),
    }),
  ],
  controllers: [ClassificationsController, MountainController],
  providers: [],
})
export class AppModule {}
