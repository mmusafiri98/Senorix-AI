streamlit run streamlit_app.py
```

### **Step 2: Genera musica**
1. Scrivi paroles o genera con AI
2. Click "GÉNÉRER LA MUSIQUE"
3. **Guarda gli expander debug**

### **Step 3: Analizza gli errori**

**Se vedi:**
```
❌ Erreur Specifique: Parameter `lrc` is invalid
```
→ **Problema:** Formato LRC sbagliato
→ **Soluzione:** Guarda l'expander "Debug: Formato LRC"

**Se vedi:**
```
❌ Erreur Specifique: GPU out of memory
```
→ **Problema:** GPU effettivamente occupato
→ **Soluzione:** Riduci steps a 8

**Se vedi:**
```
❌ Erreur Specifique: Connection timeout
```
→ **Problema:** DiffRhythm2 non risponde
→ **Soluzione:** Riprova tra 30 secondi

---

## 📋 Checklist Debug

- [ ] DiffRhythm2 è connesso? (vedi messaggio "✅ Connecté")
- [ ] Formato LRC è corretto? (guarda expander debug)
- [ ] Paroles sono valide? (vedi metrics: Mots, Lignes, Status)
- [ ] Errore specifico dice cosa? (non solo "GPU occupato")
- [ ] Stack trace mostra dettagli? (expander "Stack Trace")

---

## 🎯 Test Manuale

**Prova questo testo minimo:**
```
I love you
You love me
We are happy
Together forever

