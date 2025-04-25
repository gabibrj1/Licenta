import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { ForumService, Topic, Post, PaginatedResponse } from '../../services/forum.service';
import { AuthService } from '../../services/auth.service';
import { FormControl, Validators } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { Pipe, PipeTransform } from '@angular/core';



@Component({
  selector: 'app-forum-topic',
  templateUrl: './forum-topic.component.html',
  styleUrls: ['./forum-topic.component.scss']
})
export class ForumTopicComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  topicId: number = 0;
  topicSlug: string = '';
  topic: Topic | null = null;
  posts: Post[] = [];
  currentPage = 1;
  totalPosts = 0;
  totalPages = 0;
  
  loading = { topic: true, posts: true, posting: false };
  error = { topic: false, posts: false, posting: false };
  
  replyContent = new FormControl('', [Validators.required, Validators.minLength(10)]);
  isLoggedIn = false;
  userAvatars: { [key: string]: string } = {};

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private forumService: ForumService,
    private authService: AuthService,
    private titleService: Title
  ) { }

  ngOnInit(): void {
    this.isLoggedIn = this.authService.isAuthenticated();
    this.generateUserAvatars();

    this.route.paramMap.subscribe(params => {
      this.topicSlug = params.get('slug') || '';
      this.route.queryParamMap.subscribe(queryParams => {
        const topicId = queryParams.get('id');
        if (topicId) {
          this.topicId = parseInt(topicId, 10);
          this.loadTopic();
          this.loadPosts();
        }
      });
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadTopic(): void {
    this.loading.topic = true;
    this.error.topic = false;
    
    this.forumService.getTopic(this.topicId).pipe(takeUntil(this.destroy$)).subscribe({
      next: (topic) => {
        this.topic = topic;
        this.titleService.setTitle(`${topic.title} | Forum SmartVote`);
        this.loading.topic = false;
      },
      error: (error) => {
        console.error('Error loading topic:', error);
        this.error.topic = true;
        this.loading.topic = false;
      }
    });
  }

  loadPosts(): void {
    this.loading.posts = true;
    this.error.posts = false;
    
    this.forumService.getPostsByTopic(this.topicId, this.currentPage)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: PaginatedResponse<Post>) => {
          this.posts = response.results;
          this.totalPosts = response.count;
          this.totalPages = Math.ceil(response.count / 20);
          this.loading.posts = false;
        },
        error: (error) => {
          console.error('Error loading posts:', error);
          this.error.posts = true;
          this.loading.posts = false;
        }
      });
  }

  submitReply(): void {
    if (this.replyContent.invalid || !this.topic) return;
    
    this.loading.posting = true;
    this.error.posting = false;
    
    this.forumService.createPost(this.topic.id, this.replyContent.value || '')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.replyContent.reset();
          this.loadPosts();
          this.loading.posting = false;
        },
        error: (error) => {
          console.error('Error submitting reply:', error);
          this.error.posting = true;
          this.loading.posting = false;
        }
      });
  }

  generateUserAvatars(): void {
    const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'];
    const userData = this.authService.getUserData();
    const userEmail = userData?.email || '';
    
    this.userAvatars = {
      'admin@smartvote.ro': this.getInitialsAvatar('ADM', colors[0]),
      'moderator@smartvote.ro': this.getInitialsAvatar('MOD', colors[1]),
      'default': this.getInitialsAvatar('U', colors[4]),
    };

    if (userEmail) {
      const initials = this.getInitialsFromEmail(userEmail);
      this.userAvatars[userEmail] = this.getInitialsAvatar(initials, colors[2]);
    }
  }

  private getInitialsFromEmail(email: string): string {
    const namePart = email.split('@')[0];
    if (namePart.includes('.')) {
      const parts = namePart.split('.');
      return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
    }
    return namePart.substring(0, 2).toUpperCase();
  }

  private getInitialsAvatar(initials: string, bgColor: string): string {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 200;
    canvas.height = 200;
    
    if (context) {
      context.fillStyle = bgColor;
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.fillStyle = 'white';
      context.font = 'bold 80px Arial';
      context.textAlign = 'center';
      context.textBaseline = 'middle';
      context.fillText(initials, canvas.width/2, canvas.height/2);
    }
    
    return canvas.toDataURL('image/png');
  }

  getUserAvatar(email: string): string {
    return this.userAvatars[email] || this.userAvatars['default'];
  }

  getTimeAgo(dateString: string): string {
    return this.forumService.getTimeAgo(dateString);
  }
}
