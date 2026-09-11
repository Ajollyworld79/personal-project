# React/TypeScript-migrering med produktionens design

## Aftalt retning

Siden skal se ud som [produktionen](https://gustavchristensen.dev/). Det tidligere redesign er erstattet af en direkte konvertering af originalens markup og CSS til React. Design-skillen bruges til kontrol, ikke til at ændre det aftalte udtryk.

## Implementering

- De oprindelige `site.css` og `portfolio.css` er genskabt fra repository-versionen.
- Originalens Google Fonts-indlæsning med alle anvendte vægte er tilbage. De fire lokale fontfiler fra første redesign dækkede ikke de samme vægte.
- Navigation, hero, terminalchat, statistik, teknologilogoer, status, projekter, About, GitHub-graf og footer bruger originalens struktur, klasser og rækkefølge.
- Projekt-templateens særskilte CSS gælder kun Projects. `:where()` bevarer den oprindelige selector-prioritet, så kortenes padding ikke ændres.
- About bruger originalens `timeline`, `timeline-item` og `timeline-content`. Cirklernes position udledes dermed af den korrekte struktur.
- React 19.3, TypeScript 7.0.2, prerendering og Python-API'er er bevaret. Der er ikke deployet.

## Direkte sammenligning af baseline før designpolering

Produktionen og den lokale side er målt i Chrome ved 1440 × 1000 og 390 × 1000. De sammenlignede elementer omfatter fontfamilie, fontstørrelse, fontvægt, linjehøjde, x/y-position, bredde og højde.

| Side | Resultat |
| --- | --- |
| Forside | Ingen forskelle i de målte egenskaber for navigation, hero-overskrift, introtekst, chatramme, chatprompt, teknologikort/logo, featured-kort/overskrift, statusramme, videogitter og GitHub-kort. |
| About | Ingen forskelle i de målte egenskaber for titel, profilområde, informationskort, tidslinje, stillinger, datoer, teknologimærker, certifikatkort og uddannelsesliste. |
| Projects, desktop | Ingen forskelle i de målte egenskaber for gitter, første projektkort, titel, teknologimærke og projektbillede. |
| Projects, mobil | Samme mål for de kontrollerede kortdetaljer. Hele gitteret er ca. 26 pixels højere på grund af den opdaterede React/TypeScript-beskrivelse af selve portfolioen. |

Dette er konkrete målinger og visuel sammenligning, ikke en garanti for pixelidentiske skærmbilleder: live-data, billedindhold, animationstidspunkt og font-rendering kan variere.

## Efterfølgende godkendte designforbedringer

Brugeren har derefter godkendt alle syv mindre forbedringer. De ligger i `frontend/design-polish.css` samt chatstatus og mobilnavigationens label. Originalens CSS-filer er fortsat uændrede.

1. Mere kontrast på dæmpet tekst, herunder undertitel, datoer og hjælpetekst.
2. Læsbare aktive knapper og en tydeligt mere afdæmpet Private repo-tilstand.
3. Ensartet minimumsstørrelse på de berørte små status- og GitHub-tekster samt projektmærker.
4. Strammere afstande i projektkort og handlinger placeret nederst; alle tekster og teknologier er bevaret.
5. Ens 16:9-billedrammer med hele billeder og diagrammer synlige.
6. Synlig chatstatus: Ready, Searching CV…, Writing… og Try again, med bevaret terminalglød.
7. Synlig Navigation-label og tydeligere kant omkring mobilmenuen.

Baseline-tabellen ovenfor dokumenterer tilstanden før disse godkendte ændringer; den beskriver ikke de nye afstande og størrelser.

## Bevidste forskelle

- YouTube åbner fortsat i den ønskede dialog ved klik. Rammen og placeringen følger produktionen.
- Tidslinjens store markører er centreret præcist på både desktop og mobil. Originalen havde en mobilafvigelse på 1 pixel; den er rettet med én afgrænset CSS-regel. De fem mindre markører er allerede centrerede.
- Fejltilstande, tastaturbetjening, sikker chatmarkdown og korrekt GitHub-dataformat er bevaret. Manglende GitHub-data giver en forklaring i stedet for en skjult sektion.
- Lokalt kan GitHub-statistik hentes fra det allerede offentlige produktionsendpoint med `GITHUB_ACTIVITY_PREVIEW=1`. Produktion bruger fortsat sit eget token.
- Projektet om denne hjemmeside beskriver den nye stack. Øvrige projekttekster er bevaret.

## Kontrol

TypeScript og produktionsbygning er kontrolleret. Browsertestene dækker fire skærmbredder, navigation uden JavaScript, stor tekst, video/diagram-dialoger, chat, GitHub og centrering af alle otte tidslinjemarkører på desktop og mobil. Backend-tests dækker routes, assets, PDF og GitHub-preview.

Docker er ikke installeret lokalt, så Docker-imaget er ikke kørt. API-afhængige interaktionstests bruger kontrollerede svar; den visuelle sammenligning bruger også rigtige status- og GitHub-data.

Lokalt preview: http://127.0.0.1:8000
