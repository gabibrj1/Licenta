import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-delete-confirm.dialog',
  templateUrl: './delete-confirm.dialog.component.html',
  styleUrl: './delete-confirm.dialog.component.scss'
})
export class DeleteConfirmDialogComponent {
  constructor(public dialogRef: MatDialogRef<DeleteConfirmDialogComponent>) {}

  onNoClick(): void {
    this.dialogRef.close(false); // Returneaza "false" daca utilizatorul apasa pe "Nu"
  }

  onYesClick(): void {
    this.dialogRef.close(true); // Returnează "true" daca utilizatorul apasa pe "Da"
  }
}