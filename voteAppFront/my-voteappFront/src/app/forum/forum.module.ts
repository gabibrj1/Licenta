import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { LinkyModule } from 'ngx-linky';

// Componente forum
import { ForumCategoryComponent } from './forum-category/forum-category.component';
import { ForumTopicComponent } from './forum-topic/forum-topic.component';
import { ForumNewTopicComponent } from './forum-new-topic/forum-new-topic.component';
import { ForumNotificationsComponent } from './forum-notifications/forum-notifications.component';



@NgModule({
  declarations: [
    ForumCategoryComponent,
    ForumTopicComponent,
    ForumNewTopicComponent,
    ForumNotificationsComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    ReactiveFormsModule,
    LinkyModule
  ],
  exports: [
    ForumCategoryComponent,
    ForumTopicComponent,
    ForumNewTopicComponent,
    ForumNotificationsComponent
  ]
})
export class ForumModule { }