from django import forms

class EmailListForm(forms.Form):
    emails = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10, 'cols': 50}),
        label="Adrese Email",
        help_text="Introduceți adresele de email separate prin virgulă, linie nouă sau spațiu."
    )
    
    def clean_emails(self):
        """Validează și formatează lista de emailuri"""
        data = self.cleaned_data['emails']
        
        if not data or data.strip() == '':
            raise forms.ValidationError("Lista de email-uri nu poate fi goală.")
            
        # Înlocuiește toate separatoarele posibile cu virgule
        for sep in ['\n', '\r', ' ', ';']:
            data = data.replace(sep, ',')
        
        # Împarte și curăță lista
        emails = [email.strip() for email in data.split(',') if email.strip()]
        
        if not emails:
            raise forms.ValidationError("Nu s-au găsit adrese de email valide în lista furnizată.")
        
        # Validează formatul fiecărui email
        invalid_emails = []
        for email in emails:
            try:
                forms.EmailField().clean(email)
            except forms.ValidationError:
                invalid_emails.append(email)
        
        if invalid_emails:
            raise forms.ValidationError(
                f"Următoarele adrese email nu sunt valide: {', '.join(invalid_emails)}"
            )
        
        return emails