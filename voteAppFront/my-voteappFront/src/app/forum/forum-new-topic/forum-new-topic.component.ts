import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { ForumService, Category } from '../../services/forum.service';
import { AuthService } from '../../services/auth.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-forum-new-topic',
  templateUrl: './forum-new-topic.component.html',
  styleUrls: ['./forum-new-topic.component.scss']
})
export class ForumNewTopicComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  categories: Category[] = [];
  form: FormGroup;
  loading = false;
  error = false;
  categoryId?: number;
  
  // Proprietăți pentru mesajul de confirmare
  showResultMessage = false;
  submitSuccess = false;

  constructor(
    private fb: FormBuilder,
    private forumService: ForumService,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private titleService: Title
  ) {
    this.form = this.fb.group({
      title: ['', [Validators.required, Validators.minLength(10)]],
      content: ['', [Validators.required, Validators.minLength(20)]],
      category: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.titleService.setTitle('Creează subiect nou | Forum SmartVote');
    this.loadCategories();
    
    this.route.queryParamMap.subscribe(params => {
      const categoryId = params.get('category');
      if (categoryId) {
        this.categoryId = parseInt(categoryId, 10);
        this.form.patchValue({ category: this.categoryId });
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadCategories(): void {
    this.forumService.getCategories()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (categories) => {
          this.categories = categories;
        },
        error: (error) => {
          console.error('Eroare la încărcarea categoriilor:', error);
        }
      });
  }
  
  public navigateToForumuri(): void {
    this.router.navigate(['/menu/forumuri']);
  }

  onSubmit(): void {
    if (this.form.invalid) return;
    
    this.loading = true;
    this.error = false;
    
    const formData = this.form.value;
    
    this.forumService.createTopic({
      title: formData.title,
      content: formData.content,
      category: formData.category
    }).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (topic) => {
          // Afișăm mesajul de succes
          this.submitSuccess = true;
          this.showResultMessage = true;
          this.loading = false;
          
          // Redirecționăm după o scurtă întârziere
          setTimeout(() => {
            // Folosim window.location.href pentru o redirecționare sigură
            const baseUrl = window.location.origin; // Obține baza URL-ului (ex: https://example.com)
            const redirectUrl = `${baseUrl}/menu/forum/topic/${topic.slug}?id=${topic.id}`;
            
            console.log('Redirecționare către:', redirectUrl); // Pentru debug
            window.location.href = redirectUrl;
            
            // Alternativ, ca backup
            if (!topic.slug || !topic.id) {
              // Dacă din orice motiv topic.slug sau topic.id lipsesc, revenim la forumuri
              console.error('Lipsesc informații necesare pentru redirecționare');
              window.location.href = `${baseUrl}/menu/forumuri`;
            }
          }, 2000); // 2 secunde întârziere
        },
        error: (error) => {
          console.error('Eroare la crearea subiectului:', error);
          this.error = true;
          this.loading = false;
          
          // Afișăm mesajul de eroare
          this.submitSuccess = false;
          this.showResultMessage = true;
          
          // Ascundem mesajul de eroare după un timp
          setTimeout(() => {
            this.showResultMessage = false;
          }, 3000); // 3 secunde
        }
      });
  }
}