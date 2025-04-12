@echo off
echo Dezactivez temporar Windows Firewall...
netsh advfirewall set allprofiles state off

echo Pornesc serverul Angular...
start cmd /k "cd C:\Users\brj\Desktop\voteAppFront\my-voteappFront && ng serve --host 0.0.0.0 --disable-host-check --open"

echo.
echo Serverul Angular a pornit! Sistemul de vot este acum accesibil in reteaua locala.
echo Nu uita sa pornesti si serverul Django din VS Code.
echo Adresa pentru distribuire: http://192.168.29.140:4200
echo.
echo Nu uita sa reactivezi Windows Firewall dupa ce ai terminat testarea
echo folosind comanda: netsh advfirewall set allprofiles state on
echo.
pause