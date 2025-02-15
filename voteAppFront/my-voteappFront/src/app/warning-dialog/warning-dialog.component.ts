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
    this.dialogRef.close(); // Nu trimite nicio valoare, doar închide dialogul
  }

  onContinue(): void {
    if (this.conditionsAccepted) {
      this.dialogRef.close(true); // Trimite `true` doar dacă utilizatorul a bifat checkbox-ul și a apăsat "Continuă"
    } else {
      this.showErrorMessage = true;
    }
  }
}
