import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-gdpr-dialog',
  templateUrl: './gdpr-dialog.component.html',
  styleUrls: ['./gdpr-dialog.component.scss']
})
export class GdprDialogComponent {
  constructor(private dialogRef: MatDialogRef<GdprDialogComponent>) {}

  onAgree(): void {
    this.dialogRef.close(true); // returneaza true daca utilizatorul este de acord
  }

  onCancel(): void {
    this.dialogRef.close(false); // returneaza true daca utilizatorul anuleaza
  }
}
