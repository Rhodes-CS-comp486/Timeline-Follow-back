# Timeline-Follow-back

Planning
- [Trello Board](https://trello.com/b/tcyX6Hem/senior-sem)
- [Senior Sem](https://docs.google.com/document/d/1RZ7hgsHVpGZadd8hTEZ75BUZx71xfGUVh7zlhKFYYoE/edit?usp=sharing)
- [Team Standards](https://docs.google.com/document/d/11vJnfsCzCGU9OZnrNdWIGgBXSqHma-FAt7PTO7oOGII/edit?usp=sharing)
- [Engineering Practices](https://docs.google.com/document/d/14BOaVf0IWfEH6yW2w1v3R_5GMb58vNaGcfpaLH6x6po/edit?usp=sharing)
- [Product Design](https://docs.google.com/document/d/1t0TvrdxhJAA1PJD-_1MGH9RVdClQIZkgSDIoP2J4ruE/edit?usp=sharing)

Sprints
- [Sprint 1](https://docs.google.com/document/d/10a8ML0ZlPlMTvZuAKKrouOHfeLp4OtrIf0Bou-fFjxg/edit?usp=sharing)
- [Sprint 2](https://docs.google.com/document/d/10DOS5v4IT1fR6m0kvhi1vDr2VwHIyLmCBo4GbKtfjGE/edit?usp=sharing)
- [Sprint 3](https://docs.google.com/document/d/1ZToECIw66xyvSD3fEioZY-AY3svtOMPfmY7L_UWrgiI/edit?usp=sharing)
- [Sprint 4](https://docs.google.com/document/d/1DAAOaUlRy1jiaKCtWW2kcNF49yYj_ri2TIC1fxRfVPs/edit?usp=sharing)
- [Sprint 5](https://docs.google.com/document/d/1-VVmFNJGli5hRTtcdsIRgnvHPx4deJDouga1k1i-3n4/edit?usp=sharing)

Slideshows
- [Mid-Semester Slideshow](https://docs.google.com/presentation/d/1oa4ge7Kv9xXsgHoBk9u0-2Guwie36OXVhX3_5XdY81g/edit?usp=sharing)


# Flask + Gunicorn + Nginx Deployment Guide

## 1. Connect to Your Server
```bash
ssh timelinefollowback.com (use another server at handover)
```

---

## 2. Update & Install Dependencies
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv python3-full git nginx libpq-dev python3-dev -y
```

---

## 3. Add SSH Key for GitHub (Optinal if already done)

Generate an SSH key on your server:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```
Press `Enter` through all prompts to use defaults.

Print your public key:
```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the output, then go to **GitHub → Settings → SSH and GPG keys → New SSH key**, paste it in and save.

Test the connection:
```bash
ssh -T git@github.com
```
You should see: `Hi your-username! You've successfully authenticated...`

---

## 4. Clone Your GitHub Repo
```bash
cd ~
git clone git@github.com:your-username/your-repo.git timeline
cd timeline
```

---

## 5. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

---


## 6. Create `.env` File
```bash
nano .env
```

Add your environment variables:
```
DATABASE_URL=postgresql://username:password@host:5432/dbname
SECRET_KEY=your_secret_key_here
```
`CTRL+X`, `Y`, `Enter` to save.

> Make sure `.env` is in your `.gitignore` so secrets are never pushed to GitHub:
> ```bash
> echo ".env" >> .gitignore
> ```

---

## 7. Test Gunicorn
```bash
set -a && source .env && set +a
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

Visit `http://your_server_ip:8000` to confirm it works, then `CTRL+C` to stop.

---

## 8. Create the Systemd Service
```bash
deactivate
sudo nano /etc/systemd/system/timeline.service
```

Paste this in (replace `your_user` with your actual username):
```ini
[Unit]
Description=Gunicorn instance for Flask app
After=network.target

[Service]
User=your_user
Group=www-data
UMask=0007
WorkingDirectory=/home/your_user/timeline
EnvironmentFile=/home/your_user/timeline/.env
Environment="PATH=/home/your_user/timeline/venv/bin"
ExecStart=/home/your_user/timeline/venv/bin/gunicorn --workers 3 --bind unix:/tmp/timeline.sock wsgi:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
`CTRL+X`, `Y`, `Enter` to save.

> **Note on workers:** The recommended formula is `(2 × CPU cores) + 1`. Adjust `--workers 3` accordingly.

---

## 9. Start & Enable the Service
```bash
sudo systemctl daemon-reload
sudo systemctl start timeline
sudo systemctl enable timeline
sudo systemctl status timeline
```

Should say `Active: active (running)`. Press `Q` to exit.

Verify the socket was created:
```bash
ls -la /tmp/timeline.sock
```

---

## 10. Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/timeline
```

Paste this in:
```nginx
server {
    listen 80;
    server_name timelinefollowback.com www.timelinefollowback.com; (if different domain change this)

    location / {
        include proxy_params;
        proxy_pass http://unix:/tmp/timeline.sock;
    }
}
```
`CTRL+X`, `Y`, `Enter` to save.

```bash
sudo ln -s /etc/nginx/sites-available/timeline /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo service nginx restart
```

Visit `http://timelinefollowback.com` to confirm it works.

---

## 11. Add Free SSL (HTTPS)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d timelinefollowback.com -d www.timelinefollowback.com
```

Follow the prompts — enter your email, agree to the terms, and Certbot will automatically configure HTTPS and set up auto-renewal.

Visit `https://timelinefollowback.com` — it should be running fine.

---

## Updating Your Site in the Future

```bash
cd ~/timeline
git pull origin main
sudo systemctl restart timeline
```

---

## Useful Debugging Commands

Check service status:
```bash
sudo systemctl status timeline
```

View logs:
```bash
sudo journalctl -u timeline -n 50 --no-pager
```

Check socket exists:
```bash
ls -la /tmp/timeline.sock
```

Test Nginx config:
```bash
sudo nginx -t
```

Restart everything:
```bash
sudo systemctl restart timeline
sudo service nginx restart
```
