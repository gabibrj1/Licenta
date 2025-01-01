import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-warning-dialog',
  templateUrl: './warning-dialog.component.html',
  styleUrls: ['./warning-dialog.component.scss']
})
export class WarningDialogComponent {
  conditionsAccepted = false;
  showErrorMessage = false;

  constructor(
    private dialogRef: MatDialogRef<WarningDialogComponent>
  ) {}
  ngOnInit() {
    // Prevent dialog from closing on backdrop click
    this.dialogRef.disableClose = true;
  }

  onClose(): void {
    if (!this.conditionsAccepted) {
      this.showErrorMessage = true;
    } else {
      this.dialogRef.close();
    }
  }

  onContinue(): void {
    if (this.conditionsAccepted) {
      this.dialogRef.close(true);
    } else {
      this.showErrorMessage = true;
    }
  }
}
