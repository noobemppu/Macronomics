# Macronomics

Macronomics on talous- ja rahoitusmarkkinoiden dataan ja sen visualisointiin keskittyvä nettisivu. Käyttäjät voivat hakea haluamaansa dataa eri datantarjoajien tietokannoista ja muodostaa niistä omia graafeja ja ladata haluamansa datan omaan käyttöönsä. Tulevaisuudessa käyttäjä voi myös valita haluamansa datan seurantalistalleen ja tilata tuoreen datan sähköpostiinsa, kun uusin data on julkaistu. Tällä hetkellä olen saanut toimimaan kolme eri dataa tarjoavaa APIa: 

 - Data Commons: Googlen alusta, joka tarjoaa paljon erilaista yhteiskuntaan, talouteen ja väestöön liittyvää dataa. Data Commons kerää datansa monista eri julkisista tietokannoista ja tarjoaa sitä eteenpäin, tarjoten samalla paljon eri toiminnallisuuksia datan käyttäjille ja ohjelmistokehittäjille.
 
 - Alpha Vantage: Tarjoaa kattavasti dataa mm. osake-, valuutta-, ja optiomarkkinoilta. Lisäksi heidän APInsa tarjoaa myös globaalin uutistarjonnan.
 
 - IMF: Maailman Valuuttarahasto tarjoaa heidän APIn (juuri uudistettu) kautta pääsyn heidän omaan tietokantaansa, josta löytyy kattavasti historiallista talousdataa lähes kaikista maailman maista.

Olen kehittänyt Marconomicsia tähän mennessä lokaalisti, koska tarkoitukseni on saada API:t ja datavisualisaation perustoiminnot käyttöön, ennen kuin lähden pystyttämään pilviympäristöä. Nyt kuitenkin perustoiminnallisuudet toimivat (vaikka kehityskohteita on vielä huomattavasti!), joten seuraavaksi pääsen vihdoinkin siirtämään sovellusta pilveen (AWS). Tarkoitukseni on hyödyntää eri AWS:n palveluita mahdollisimman kattavasti, tässä esimerkkejä (ei kuitenkaan koko arkkitehtuuri) tämän hetkisistä suunnitelmista:

 - käyttää Route53:sta DNS-palveluna
 - hyödyntää Lambdaa ja API Gateway:ta käyttäjän tekemissä API-kutsuissa.
 - ELB + EC2 Django back-endin pyörittämiseen sekä osan dataprosessoinnin suorittamiseen sekä graafien luomiseen.
 - hyödyntää DynamoDB:tä tietokantana käyttäjien seurantalistojen ja käyttäjätietojen säilyttämiseen sekä mahdollisesti myös talousdatan (esimerkiksi General Templates-osion    Most Popular Countries-datan säilyttämiseen. Toinen vaihtoehto kyseisen talousdatan säilyttämiseen olisi esim. API Gateway caching).
 - käyttää Lambdaa + SQS + SES käyttäjien datan lähettämiseen heidän sähköposteihinsa.
 - käyttää Cognitoa käyttäjien autentikaatioon.

Haluan huomauttaa (ja kuten koodistakin näkyy), että nettisivujen kehitys on vielä kesken ja lisäominaisuuksia on tulossa tulevaisuudessa. Näitä ovat mm.:

  - Kattava portfolio-työkalu, joka sisältää mm. työkaluja ja dataa riskitason arviointiin ja korrelaatiolaskurin eri omaisuusluokkien välille.
  - Uutisvirta yhdistettynä uutista koskevaan dataan (esim. etsin USA:n inflaatio-dataa, joten datan lisäksi nettisivu näyttää viimeisimpiä inflaatioon liittyviä uutisia)
  - Käyttäjän omat seurantalistat sekä mahdollisuus lähettää niitä sähköpostiin (mainittu myös ylempänä)
  - Mahdollisuus datan kopioimiseen suoraan Exceliin

Myös nettisivujen ulkoasu on vielä hyvin yksinkertainen ja pyrin parantamaan sitä jatkuvasti.

Keskutelen mielelläni lisää projektin kehityksestä ja teknologisista ratkaisuista! Tämä esittely kuvastaa tämän hetken suunnitelmaa ja mahdollisia muutoksia todennäköisesti tulee.
   
