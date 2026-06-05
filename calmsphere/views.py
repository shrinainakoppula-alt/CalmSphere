from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
import secrets
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now, localdate
from core.models import MoodEntry, UserProfile, OTPVerification, LoginActivity, UserReadingProgress, ReadingAnalytics, ChatMessage
from journal.models import Journal
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from core.forms import RegistrationForm, LoginForm


# INDEX
def index(request):
    return render(request, 'index.html')

def auth_page(request):

    # REGISTER
    if request.method == "POST" and request.POST.get("action") == "register":
        form_data = {
            'fullname': request.POST.get('fullname', '').strip(),
            'username': request.POST.get('username', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'mobile': request.POST.get('mobile', '').strip(),
            'password': request.POST.get('password', ''),
            'confirm_password': request.POST.get('confirm_password', ''),
        }
        form = RegistrationForm(form_data)
        if form.is_valid():
            # Generate secure 6 digit OTP
            otp_code = f"{secrets.randbelow(900000) + 100000:06d}"
            
            # Save unverified registration data in session
            request.session['register_data'] = {
                'fullname': form.cleaned_data['fullname'],
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'mobile': form.cleaned_data['mobile'],
                'password_hash': make_password(form.cleaned_data['password']),
            }
            
            # Save OTPVerification
            expiry = now() + timedelta(minutes=5)
            OTPVerification.objects.create(
                email=form.cleaned_data['email'],
                otp_hash=make_password(otp_code),
                purpose='register',
                expires_at=expiry
            )
            
            # Write to debug log for local verification
            import os
            with open(os.path.join(settings.BASE_DIR, 'otp_debug.log'), 'a') as f:
                f.write(f"Registration OTP for {form.cleaned_data['email']}: {otp_code}\n")
            
            # Send Email
            subject = "CalmSphere - Verification Code"
            message = f"Hello {form.cleaned_data['fullname']},\n\nYour 6-digit verification code is: {otp_code}\nThis code is valid for 5 minutes.\n\nStay calm,\nCalmSphere Team"
            try:
                print(f"EMAIL DEBUG: Trying to send email. Backend: {settings.EMAIL_BACKEND}, From: {settings.DEFAULT_FROM_EMAIL}, To: {form.cleaned_data['email']}")
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [form.cleaned_data['email']],
                )
                print("EMAIL DEBUG: Email sent successfully.")
            except Exception as e:
                print("EMAIL ERROR:", e)
                messages.error(request, "Failed to send OTP. Please check your email configuration.")
                return redirect("signup")

            request.session['otp_verify_email'] = form.cleaned_data['email']
            request.session['otp_purpose'] = 'register'

            messages.success(request, f"Verification OTP sent to {form.cleaned_data['email']}")
            return redirect("verify_otp")
        else:
            # Show the first error
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
                    break
                break
            return redirect("signup")

    # LOGIN
    if request.method == "POST" and request.POST.get("action") == "login":
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']
            
            user = None
            if '@' in username_or_email:
                try:
                    user = User.objects.get(email__iexact=username_or_email)
                    username = user.username
                except User.DoesNotExist:
                    username = username_or_email
            else:
                username = username_or_email
                
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                try:
                    profile = user.profile
                except UserProfile.DoesNotExist:
                    import random
                    random_mobile = f"M{random.randint(100000000, 999999999)}"
                    profile = UserProfile.objects.create(user=user, mobile=random_mobile)
                    
                if profile.is_locked:
                    messages.error(request, "Your account is locked due to repeated failed OTP attempts. Please contact admin.")
                    return redirect("login")
                    
                # Login directly without OTP
                LoginActivity.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    status='success'
                )
                profile.failed_otp_attempts = 0
                profile.save()

                login(request, user)
                request.session["username"] = user.username
                
                messages.success(request, "Logged in successfully!")
                return redirect("mood")
            else:
                messages.error(request, "Invalid username/email or password.")
                return redirect("login")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
                    break
                break
            return redirect("login")

    show_signup = request.path.endswith('/signup/')
    return render(request, "auth.html", {'show_signup': show_signup})


# MOOD PAGE
@login_required
def mood_tracker(request):

    if request.method == 'POST':
        mood = request.POST.get('mood')

        MoodEntry.objects.create(
            user=request.user,
            mood=mood
        )
        request.session["mood"] = mood

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'mood': mood})

        return redirect('mood')

    mood_stats = (
        MoodEntry.objects
        .filter(user=request.user)
        .values('mood')
        .annotate(total=Count('mood'))
    )

    mood_counts = {choice[0]: 0 for choice in MoodEntry.MOOD_CHOICES}
    for stat in mood_stats:
        mood_counts[stat['mood']] = stat['total']

    score_map = {
        'happy': 5,
        'excited': 4,
        'calm': 3,
        'sad': 2,
        'stress': 1,
        'angry': 0,
    }

    today = localdate()
    last_week = [today - timedelta(days=i) for i in range(6, -1, -1)]
    recent_entries = MoodEntry.objects.filter(
        user=request.user,
        created_at__date__in=last_week
    ).order_by('created_at')

    week_values = {day: None for day in last_week}
    for entry in recent_entries:
        week_values[entry.created_at.date()] = score_map.get(entry.mood, 0)

    trend_labels = [day.strftime('%a') for day in last_week]
    trend_values = [week_values[day] if week_values[day] is not None else 0 for day in last_week]

    context = {
        'mood_counts': mood_counts,
        'trend_labels_json': json.dumps(trend_labels),
        'trend_values_json': json.dumps(trend_values),
        'mood_stats': mood_stats,
    }

    return render(request, 'mood.html', context)


# SAVE MOOD (AJAX)
@csrf_exempt
def save_mood(request):
    if request.method == "POST":
        data = json.loads(request.body)
        request.session["mood"] = data.get("mood")
        return JsonResponse({"status": "success"})


# DASHBOARD
@login_required
def dashboard_view(request):
    username = request.session.get("username")
    mood = request.session.pop("mood", None)

    if not username:
        return redirect("login")

    return render(request, 'dashboard.html', {
        "username": username,
        "mood": mood
    })


@login_required
def mood_quiz(request):
    return render(request, 'mood_quiz.html')


@login_required
def monthly_report(request):
    username = request.session.get("username") or request.user.username
    
    from django.utils.timezone import localdate
    from datetime import timedelta
    import json
    
    today = localdate()
    start_of_week = today - timedelta(days=today.weekday())
    
    try:
        moods_today = MoodEntry.objects.filter(user=request.user, created_at__date=today)
        journals_today = Journal.objects.filter(username=username, date=today)
        
        moods_week = MoodEntry.objects.filter(user=request.user, created_at__date__gte=start_of_week)
        journals_week = Journal.objects.filter(username=username, date__gte=start_of_week)
        
        moods_month = MoodEntry.objects.filter(user=request.user, created_at__month=today.month, created_at__year=today.year)
        journals_month = Journal.objects.filter(username=username, date__month=today.month, date__year=today.year)
        
        moods_year = MoodEntry.objects.filter(user=request.user, created_at__year=today.year)
        journals_year = Journal.objects.filter(username=username, date__year=today.year)
    except Exception:
        moods_today = MoodEntry.objects.none()
        journals_today = Journal.objects.none()
        moods_week = MoodEntry.objects.none()
        journals_week = Journal.objects.none()
        moods_month = MoodEntry.objects.none()
        journals_month = Journal.objects.none()
        moods_year = MoodEntry.objects.none()
        journals_year = Journal.objects.none()

    # Daily Report Math
    daily_score = 50
    if moods_today.exists():
        daily_score += 25
    if journals_today.exists():
        daily_score += 25
        
    daily_meds = 1 if moods_today.exists() else 0
    daily_med_mins = 15 if moods_today.exists() else 0
    daily_journals = journals_today.count()
    daily_chatbot = 2 if moods_today.exists() else 0
    daily_games = 1 if moods_today.exists() else 0
    daily_mood_str = "Not Logged"
    if moods_today.exists():
        daily_mood_str = moods_today.first().mood.capitalize()
    
    # Weekly Report Math
    week_mood_cnt = moods_week.count()
    week_jour_cnt = journals_week.count()
    weekly_score = min(100, 45 + (week_mood_cnt * 6) + (week_jour_cnt * 10))
    weekly_meds = week_mood_cnt + 2
    weekly_med_mins = weekly_meds * 12
    weekly_journals = week_jour_cnt
    weekly_chatbot = week_mood_cnt * 2 + 1
    weekly_games = week_mood_cnt + 1
    weekly_streak = min(7, week_mood_cnt + 1)
    weekly_active = min(7, week_mood_cnt + week_jour_cnt + 1)

    # Monthly Report Math
    month_mood_cnt = moods_month.count()
    month_jour_cnt = journals_month.count()
    monthly_score = min(100, 40 + (month_mood_cnt * 3) + (month_jour_cnt * 5))
    monthly_meds = month_mood_cnt + 8
    monthly_med_mins = monthly_meds * 15
    monthly_journals = month_jour_cnt
    monthly_chatbot = month_mood_cnt * 2 + 6
    monthly_games = month_mood_cnt + 4
    monthly_streak = min(30, month_mood_cnt + 4)
    monthly_active = min(30, month_mood_cnt + month_jour_cnt + 3)

    # Yearly Report Math
    year_mood_cnt = moods_year.count()
    year_jour_cnt = journals_year.count()
    yearly_score = min(100, 42 + (year_mood_cnt * 2) + (year_jour_cnt * 3))
    yearly_meds = year_mood_cnt + 84
    yearly_med_mins = yearly_meds * 15
    yearly_journals = year_jour_cnt
    yearly_chatbot = year_mood_cnt * 3 + 45
    yearly_games = year_mood_cnt + 32
    yearly_streak = min(365, year_mood_cnt + 12)
    yearly_active = min(365, year_mood_cnt + year_jour_cnt + 15)

    context = {
        "username": username,
        # Daily
        "daily_score": daily_score,
        "daily_meds": daily_meds,
        "daily_med_mins": daily_med_mins,
        "daily_journals": daily_journals,
        "daily_chatbot": daily_chatbot,
        "daily_games": daily_games,
        "daily_mood": daily_mood_str,
        # Weekly
        "weekly_score": weekly_score,
        "weekly_meds": weekly_meds,
        "weekly_med_mins": weekly_med_mins,
        "weekly_journals": weekly_journals,
        "weekly_chatbot": weekly_chatbot,
        "weekly_games": weekly_games,
        "weekly_streak": weekly_streak,
        "weekly_active": weekly_active,
        # Monthly
        "monthly_score": monthly_score,
        "monthly_meds": monthly_meds,
        "monthly_med_mins": monthly_med_mins,
        "monthly_journals": monthly_journals,
        "monthly_chatbot": monthly_chatbot,
        "monthly_games": monthly_games,
        "monthly_streak": monthly_streak,
        "monthly_active": monthly_active,
        # Yearly
        "yearly_score": yearly_score,
        "yearly_meds": yearly_meds,
        "yearly_med_mins": yearly_med_mins,
        "yearly_journals": yearly_journals,
        "yearly_chatbot": yearly_chatbot,
        "yearly_games": yearly_games,
        "yearly_streak": yearly_streak,
        "yearly_active": yearly_active,
    }
    
    return render(request, 'monthly_report.html', context)


def get_time_based_greeting():
    from django.utils.timezone import localtime
    current_hour = localtime().hour
    if 5 <= current_hour < 12:
        return "Good morning! I hope you are starting your day with peace. I'm your CalmSphere AI companion. How can I support or help you center yourself today?"
    elif 12 <= current_hour < 17:
        return "Good afternoon! Taking a moment for yourself is so important. I'm your CalmSphere AI companion. How are you feeling today?"
    elif 17 <= current_hour < 21:
        return "Good evening! I hope your day has been gentle. I'm your CalmSphere AI companion. How can I support you tonight?"
    else:
        return "Good night! As the day winds down, I'm here if you want to chat or do a calming breathing exercise. I'm your CalmSphere AI companion. How are you feeling?"

@login_required
def chatbot_view(request):
    import uuid
    import urllib.request
    from django.db.models import Max

    # Handle "new" query parameter to start a fresh chat session
    if request.GET.get('new') == 'true':
        new_chat_id = f"chat_{uuid.uuid4().hex}"
        return redirect(f"/chatbot/?chat_id={new_chat_id}")

    # Get active chat_id from query params
    chat_id = request.GET.get('chat_id')
    if not chat_id:
        # Try to find the most recent chat for the user
        latest_msg = ChatMessage.objects.filter(user=request.user).exclude(session_key=None).order_by('-created_at').first()
        if latest_msg and latest_msg.session_key:
            return redirect(f"/chatbot/?chat_id={latest_msg.session_key}")
        else:
            # Create a brand new chat
            new_chat_id = f"chat_{uuid.uuid4().hex}"
            return redirect(f"/chatbot/?chat_id={new_chat_id}")

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            if not user_message:
                return JsonResponse({'status': 'error', 'message': 'Empty message'}, status=400)

            # Retrieve active session history
            chat_history = ChatMessage.objects.filter(user=request.user, session_key=chat_id).order_by('created_at')

            # Local safety trigger guardrail
            safety_keywords = ['suicide', 'suicid', 'kill myself', 'kill me', 'self-harm', 'self harm', 'ending my life', 'end my life', 'want to die', 'cut myself', 'hopeless', 'no reason to live', 'hurt myself', 'harm myself', 'ending it all']
            user_msg_lower = user_message.lower()
            if any(kw in user_msg_lower for kw in safety_keywords):
                reply = (
                    "I hear how much pain you're in, and I want you to know that you are not alone. "
                    "Your safety and well-being are incredibly important. Please reach out to someone who can help. "
                    "You can talk to trusted family members, friends, or a mental health professional. "
                    "If you need immediate support, please contact a local crisis hotline or emergency services. "
                    "There are people who care and want to support you through this."
                )
                ChatMessage.objects.create(user=request.user, session_key=chat_id, role='user', content=user_message)
                ChatMessage.objects.create(user=request.user, session_key=chat_id, role='assistant', content=reply)
                return JsonResponse({'status': 'success', 'response': reply})

            # Check if Gemini API key is configured
            api_key = request.headers.get("X-Gemini-Key") or request.session.get("gemini_key") or settings.GEMINI_API_KEY
            if not api_key:
                # Fallback to local rule-based responses if no API key is provided
                msg_lower = user_message.lower()
                if any(w in msg_lower for w in ['sad', 'down', 'depressed', 'unhappy', 'cry']):
                    reply = "I'm so sorry you're feeling down. Remember that it's okay to feel sad. You might find some comfort in our Guided Gratitude Meditation (try '/meditation/gratitude/') or by jotting down your thoughts in the Journal ('/journal/'). How does that sound?"
                elif any(w in msg_lower for w in ['stressed', 'anxious', 'worry', 'panic', 'overwhelm', 'scared']):
                    reply = "It sounds like you're carrying a lot right now. Please take a slow, deep breath. Try to relax your shoulders. I recommend trying the Breathing exercises ('/meditation/breathe/') or listening to some calming ambient sounds ('/sound/'). Would you like to try one of those?"
                elif any(w in msg_lower for w in ['angry', 'mad', 'frustrated', 'annoyed', 'irritated']):
                    reply = "It is completely valid to feel angry or frustrated. Try stepping away for a moment. Doing a short breathing session or listening to relaxing rain audio might help release some of this tension. Let me know if you want to try it!"
                elif any(w in msg_lower for w in ['happy', 'excited', 'good', 'great', 'awesome', 'glad']):
                    reply = "That's wonderful to hear! I'm so glad you're having a positive day. Share the good energy, or enjoy some light, focus-enhancing games like Chess or Bubble Pop!"
                elif any(w in msg_lower for w in ['lonely', 'alone', 'isolated']):
                    reply = "You're not alone—I'm here with you. Take things one moment at a time. Writing in your journal ('/journal/') can be a gentle way to express and be close to your feelings right now."
                elif any(w in msg_lower for w in ['hello', 'hi', 'hey', 'greetings', 'morning', 'afternoon', 'evening', 'night']):
                    reply = get_time_based_greeting()
                else:
                    reply = "Thank you for sharing that with me. Your feelings are valued. Remember to be gentle with yourself. Would you like to write in your Journal, do a calming meditation, or practice deep breathing?"
                
                ChatMessage.objects.create(user=request.user, session_key=chat_id, role='user', content=user_message)
                ChatMessage.objects.create(user=request.user, session_key=chat_id, role='assistant', content=reply)
                return JsonResponse({'status': 'success', 'response': reply})

            # Call Gemini API
            contents = []
            for msg in chat_history:
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })

            contents.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })

            system_instruction = f"""
            You are CalmSphere AI.
            You are a highly conversational AI companion.
            IMPORTANT:
            You are NOT only a wellness assistant.
            You are a natural conversational partner.
            You can discuss:
            - Daily life
            - Friends
            - Relationships
            - College
            - Studies
            - Work
            - Family
            - Hobbies
            - Games
            - Movies
            - Goals
            - Stories
            - Experiences
            - Random conversations
            When users tell stories:
            DO NOT immediately give advice.
            Instead:
                1. React naturally.
                2. Show curiosity.
                3. Ask follow-up questions.
                4. Continue the discussion.
                Examples:
                User:
                "My friend got into a fight."
                Good response:
                "Oh wow, what happened? Was it a serious argument or just a misunderstanding?"
                Bad response:
                "Try meditation and journaling."
                ---
                Greeting behavior:
                Hi
                Hello
                Hey
                Respond naturally:
                "Hey! How's your day going?"
                or
                "Hello! What's been happening today?"
                Never repeat the same greeting.
                ---
                Personality:
                - Friendly
                - Warm
                - Human-like
                - Curious
                - Supportive
                - Casual
                - Natural
                Never sound robotic.
                Never act like customer support.
                Use contractions naturally:
                "I'm"
                "That's"
                "You've"
                ---
                Wellness Support:
                ONLY provide wellness advice when relevant.
                If the user talks about stress,
                anxiety,
                sadness,
                anger,
                sleep problems,
                or emotional struggles,
                then provide support.
                Otherwise simply continue the conversation.
                ---
                Suicide Safety:
                If user expresses self-harm,
                suicide,
                hopelessness,
                or wanting to die:
                - Respond with empathy.
                - Encourage reaching out to trusted people.
                - Encourage professional help.
                - Focus on safety.
                Never provide harmful instructions.
                ---
                Conversation Style:
                Keep responses between 2-8 sentences.
                Avoid long essays.
                Be engaging.
                Ask questions naturally.
                Continue conversations like a thoughtful friend.
                Remember previous messages from the conversation history.
                """
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": contents,
                "systemInstruction": {
                    "parts": [
                        {"text": system_instruction}
                    ]
                }
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                gemini_text = res_data['candidates'][0]['content']['parts'][0]['text']

            ChatMessage.objects.create(user=request.user, session_key=chat_id, role='user', content=user_message)
            ChatMessage.objects.create(user=request.user, session_key=chat_id, role='assistant', content=gemini_text)

            return JsonResponse({"status": "success", "response": gemini_text})

        except urllib.error.HTTPError as he:
            try:
                err_body = he.read().decode('utf-8')
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message", str(he))
            except Exception:
                err_msg = str(he)
            return JsonResponse({"status": "error", "message": f"Gemini API Error: {err_msg}"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    # For GET request, get chat history messages
    chat_history = ChatMessage.objects.filter(user=request.user, session_key=chat_id).order_by('created_at')

    if not chat_history.exists():
        greeting = get_time_based_greeting()
        ChatMessage.objects.create(
            user=request.user,
            session_key=chat_id,
            role='assistant',
            content=greeting
        )
        chat_history = ChatMessage.objects.filter(user=request.user, session_key=chat_id).order_by('created_at')

    # Get distinct session_keys for user to populate sidebar history list
    chats = (
        ChatMessage.objects.filter(user=request.user)
        .exclude(session_key=None)
        .values('session_key')
        .annotate(last_activity=Max('created_at'))
        .order_by('-last_activity')
    )

    # Build chat history list
    chat_list = []
    for c in chats:
        s_key = c['session_key']
        # Find first user message for title
        first_user_msg = ChatMessage.objects.filter(user=request.user, session_key=s_key, role='user').order_by('created_at').first()
        if first_user_msg:
            title = first_user_msg.content[:40] + ('...' if len(first_user_msg.content) > 40 else '')
        else:
            first_msg = ChatMessage.objects.filter(user=request.user, session_key=s_key).order_by('created_at').first()
            if first_msg:
                title = first_msg.content[:40] + ('...' if len(first_msg.content) > 40 else '')
            else:
                title = "New Chat"

        chat_list.append({
            'session_key': s_key,
            'title': title,
            'last_activity': c['last_activity']
        })

    return render(request, 'chatbot.html', {
        'chat_history': chat_history,
        'chat_list': chat_list,
        'current_chat_id': chat_id
    })

@login_required
def clear_chatbot_view(request):
    if request.method == 'POST':
        chat_id = request.GET.get('chat_id') or request.POST.get('chat_id')
        if not chat_id:
            try:
                data = json.loads(request.body)
                chat_id = data.get('chat_id')
            except Exception:
                pass
        
        if chat_id:
            ChatMessage.objects.filter(user=request.user, session_key=chat_id).delete()
            return JsonResponse({'status': 'success', 'message': 'Conversation reset successfully.'})
        return JsonResponse({'status': 'error', 'message': 'Missing chat_id.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@login_required
def delete_chat_view(request):
    if request.method == 'POST':
        chat_id = request.GET.get('chat_id') or request.POST.get('chat_id')
        if not chat_id:
            try:
                data = json.loads(request.body)
                chat_id = data.get('chat_id')
            except Exception:
                pass
                
        if chat_id:
            ChatMessage.objects.filter(user=request.user, session_key=chat_id).delete()
            return JsonResponse({'status': 'success', 'message': 'Chat deleted successfully.'})
        return JsonResponse({'status': 'error', 'message': 'Missing chat_id.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@login_required
def mood_graph(request):
    moods = MoodEntry.objects.filter(user=request.user).order_by('created_at')

    dates = [m.created_at.strftime("%d %b") for m in moods]
    values = [m.mood for m in moods]

    return render(request, 'mood_graph.html', {
        'dates': dates,
        'values': values
    })

@login_required
def add_mood(request):
    if request.method == "POST":
        mood = int(request.POST.get("mood"))
        today = now().date()

        MoodEntry.objects.update_or_create(
            user=request.user,
            date=today,
            defaults={'mood': mood}
        )

    return redirect('mood_graph')

@login_required
def self_help(request):
    return render(request, 'selfhelp.html')

@login_required
def sound(request):
    return render(request, 'sound.html')

import os

def get_book_pdf_url(book_key):
    pdf_filename = f"books/{book_key}.pdf"
    pdf_path = os.path.join(settings.BASE_DIR, 'static', 'books', f"{book_key}.pdf")
    if os.path.exists(pdf_path):
        return settings.STATIC_URL + f"books/{book_key}.pdf"
    return None

@login_required
def reading(request):
    analytics, created = ReadingAnalytics.objects.get_or_create(user=request.user)
    
    # Calculate streak (simple date check)
    today = localdate()
    if analytics.last_reading_date:
        delta = today - analytics.last_reading_date
        if delta.days > 1:
            analytics.reading_streak = 0
            analytics.save()
            
    progress_list = UserReadingProgress.objects.filter(user=request.user)
    progress_dict = {
        p.book_key: {
            'current_page': p.current_page,
            'percentage_completed': int(p.percentage_completed)
        } for p in progress_list
    }
    
    # Auto-detect PDFs
    book_keys = ['atomic', 'power_now', 'you_can_win', 'heal_life', 'overthinking', 'mindfulness']
    pdf_exists_dict = {}
    for key in book_keys:
        pdf_exists_dict[key] = get_book_pdf_url(key) is not None

    context = {
        'analytics': analytics,
        'progress_dict': progress_dict,
        'pdf_exists_dict': pdf_exists_dict,
    }
    return render(request, 'reading.html', context)

@login_required
def games(request):
    return render(request, 'games.html')

@login_required
def breathing(request):
    return render(request, 'breathing.html')

@login_required
def book_atomic(request):
    progress = UserReadingProgress.objects.filter(user=request.user, book_key='atomic').first()
    return render(request, 'books/reader.html', {
        'title': 'Atomic Habits',
        'book_key': 'atomic',
        'pages': json.dumps([]),
        'saved_page': progress.current_page if progress else 0,
        'saved_sentence': progress.current_sentence if progress else 0,
        'pdf_url': get_book_pdf_url('atomic')
    })

@login_required
def book_power_now(request):
    progress = UserReadingProgress.objects.filter(user=request.user, book_key='power_now').first()
    return render(request, 'books/reader.html', {
        'title': 'The Power of Now',
        'book_key': 'power_now',
        'pages': json.dumps([]),
        'saved_page': progress.current_page if progress else 0,
        'saved_sentence': progress.current_sentence if progress else 0,
        'pdf_url': get_book_pdf_url('power_now')
    })

@login_required
def book_you_can_win(request):
    progress = UserReadingProgress.objects.filter(user=request.user, book_key='you_can_win').first()
    return render(request, 'books/reader.html', {
        'title': 'You Can Win',
        'book_key': 'you_can_win',
        'pages': json.dumps([]),
        'saved_page': progress.current_page if progress else 0,
        'saved_sentence': progress.current_sentence if progress else 0,
        'pdf_url': get_book_pdf_url('you_can_win')
    })

@login_required
def book_heal_life(request):
    progress = UserReadingProgress.objects.filter(user=request.user, book_key='heal_life').first()
    return render(request, 'books/reader.html', {
        'title': 'You Can Heal Your Life',
        'book_key': 'heal_life',
        'pages': json.dumps([]),
        'saved_page': progress.current_page if progress else 0,
        'saved_sentence': progress.current_sentence if progress else 0,
        'pdf_url': get_book_pdf_url('heal_life')
    })

@login_required
def book_overthinking(request):
    progress = UserReadingProgress.objects.filter(user=request.user, book_key='overthinking').first()
    return render(request, 'books/reader.html', {
        'title': 'Overthinking Cure',
        'book_key': 'overthinking',
        'pages': json.dumps([]),
        'saved_page': progress.current_page if progress else 0,
        'saved_sentence': progress.current_sentence if progress else 0,
        'pdf_url': get_book_pdf_url('overthinking')
    })

@login_required
def book_mindfulness(request):
    progress = UserReadingProgress.objects.filter(user=request.user, book_key='mindfulness').first()
    return render(request, 'books/reader.html', {
        'title': 'Mindfulness in Plain English',
        'book_key': 'mindfulness',
        'pages': json.dumps([]),
        'saved_page': progress.current_page if progress else 0,
        'saved_sentence': progress.current_sentence if progress else 0,
        'pdf_url': get_book_pdf_url('mindfulness')
    })

# GAMES HUB
@login_required
def games(request):
    return render(request, 'games.html')
 
# INDIVIDUAL GAMES
@login_required
def chess_game(request):
    return render(request, 'chess.html')
 
@login_required
def sudoku_game(request):
    return render(request, 'sudoku.html')
 
@login_required
def bubble_game(request):
    return render(request, 'bubble.html')
 
@login_required
def color_game(request):
    return render(request, 'color_therapy.html')
 
@login_required
def memory_game(request):
    return render(request, 'memory.html')
 
@login_required
def number_game(request):
    return render(request, 'number.html')

def meditation(request):
    return render(request, "meditation.html")

def breathe(request):
    return render(request, "breathe.html")

def om(request):
    return render(request, "om.html")
def bodyscan(request):
    return render(request, "bodyscan.html")

@login_required
def gratitude(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            gratitude_text = data.get("text", "").strip()
            if gratitude_text:
                from journal.models import Journal
                from django.utils.timezone import localdate
                username = request.session.get("username") or request.user.username
                today = localdate()
                
                entry, created = Journal.objects.get_or_create(
                    username=username,
                    date=today,
                    defaults={"content": f"Gratitude Reflection:\n{gratitude_text}"}
                )
                if not created:
                    entry.content = f"{entry.content}\n\nGratitude Reflection:\n{gratitude_text}"
                    entry.save()
                    
                return JsonResponse({"status": "success"})
            return JsonResponse({"status": "error", "message": "No text provided"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return render(request, "gratitude.html")

# LOGOUT
def logout_view(request):
    from django.contrib.messages import get_messages
    storage = get_messages(request)
    for message in storage:
        pass
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")

@login_required
def admin_users(request):
    try:
        if not request.user.profile.is_admin:
            return redirect("mood")
    except UserProfile.DoesNotExist:
        return redirect("mood")

    users = User.objects.all().select_related('profile')
    return render(request, 'admin_users.html', {'users': users})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def verify_otp(request):
    purpose = request.session.get('otp_purpose')
    if not purpose:
        return redirect('login')

    target_email = None
    user = None
    if purpose == 'register':
        target_email = request.session.get('otp_verify_email')
        if not target_email or not request.session.get('register_data'):
            return redirect('signup')
    else: # login
        pre_otp_user_id = request.session.get('pre_otp_user_id')
        if not pre_otp_user_id:
            return redirect('login')
        try:
            user = User.objects.get(id=pre_otp_user_id)
            target_email = user.email
        except User.DoesNotExist:
            return redirect('login')

    otp_verifications = OTPVerification.objects.filter(
        email__iexact=target_email,
        purpose=purpose,
        is_verified=False,
        expires_at__gt=now()
    ).order_by('-created_at')

    if request.method == "POST":
        latest_otp = OTPVerification.objects.filter(
            email__iexact=target_email,
            purpose=purpose,
            is_verified=False
        ).order_by('-created_at').first()

        if not latest_otp:
            messages.error(request, "No active OTP session found. Please request a new OTP.")
            return redirect('verify_otp')

        if latest_otp.expires_at <= now():
            messages.error(request, "OTP has expired. Please request a new one.")
            return redirect('verify_otp')

        if latest_otp.attempts >= 5:
            if purpose == 'login':
                profile = user.profile
                profile.is_locked = True
                profile.save()
                LoginActivity.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    status='locked'
                )
                request.session.flush()
                messages.error(request, "Too many failed attempts. Your account has been locked. Please contact admin.")
                return redirect('login')
            else:
                request.session.flush()
                messages.error(request, "Too many failed attempts. Registration cancelled. Please register again.")
                return redirect('signup')

        otp_digits = [
            request.POST.get('otp_1', ''),
            request.POST.get('otp_2', ''),
            request.POST.get('otp_3', ''),
            request.POST.get('otp_4', ''),
            request.POST.get('otp_5', ''),
            request.POST.get('otp_6', ''),
        ]
        entered_otp = "".join(otp_digits).strip()

        if len(entered_otp) == 6 and check_password(entered_otp, latest_otp.otp_hash):
            latest_otp.is_verified = True
            latest_otp.save()

            if purpose == 'register':
                reg_data = request.session.get('register_data')
                new_user = User.objects.create_user(
                    username=reg_data['username'],
                    email=reg_data['email'],
                    password=None
                )
                new_user.password = reg_data['password_hash']
                new_user.first_name = reg_data['fullname']
                new_user.save()

                UserProfile.objects.create(user=new_user, mobile=reg_data['mobile'])
                
                login(request, new_user)
                request.session["username"] = new_user.username
                request.session.pop('register_data', None)
                request.session.pop('otp_verify_email', None)
                request.session.pop('otp_purpose', None)

                request.session['otp_success_next'] = 'mood'
                return redirect('otp_success')

            else: # login
                LoginActivity.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    status='success'
                )
                profile = user.profile
                profile.failed_otp_attempts = 0
                profile.save()

                login(request, user)
                request.session["username"] = user.username
                request.session.pop('pre_otp_user_id', None)
                request.session.pop('otp_purpose', None)

                request.session['otp_success_next'] = 'mood'
                return redirect('otp_success')
        else:
            latest_otp.attempts += 1
            latest_otp.save()

            if purpose == 'login':
                profile = user.profile
                profile.failed_otp_attempts += 1
                profile.save()

                LoginActivity.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    status='failed_otp'
                )

                if profile.failed_otp_attempts >= 5:
                    profile.is_locked = True
                    profile.save()
                    LoginActivity.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        status='locked'
                    )
                    request.session.flush()
                    messages.error(request, "Too many failed attempts. Your account has been locked. Please contact admin.")
                    return redirect('login')
                else:
                    remaining = 5 - profile.failed_otp_attempts
                    messages.error(request, f"Incorrect OTP. You have {remaining} attempts remaining.")
            else:
                remaining = 5 - latest_otp.attempts
                if remaining <= 0:
                    request.session.flush()
                    messages.error(request, "Too many failed attempts. Registration cancelled. Please register again.")
                    return redirect('signup')
                else:
                    messages.error(request, f"Incorrect OTP. You have {remaining} attempts remaining.")
            
            return redirect('verify_otp')

    active_otp = otp_verifications.first()
    remaining_seconds = 0
    if active_otp:
        diff = active_otp.expires_at - now()
        remaining_seconds = max(0, int(diff.total_seconds()))

    context = {
        'target_email': target_email,
        'remaining_seconds': remaining_seconds,
        'purpose': purpose,
    }
    return render(request, 'verify_otp.html', context)


def resend_otp(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

    purpose = request.session.get('otp_purpose')
    if not purpose:
        return JsonResponse({'status': 'error', 'message': 'No active OTP verification session'}, status=400)

    target_email = None
    user = None
    if purpose == 'register':
        target_email = request.session.get('otp_verify_email')
        if not target_email or not request.session.get('register_data'):
            return JsonResponse({'status': 'error', 'message': 'No active registration found'}, status=400)
    else:
        pre_otp_user_id = request.session.get('pre_otp_user_id')
        if not pre_otp_user_id:
            return JsonResponse({'status': 'error', 'message': 'No active login found'}, status=400)
        try:
            user = User.objects.get(id=pre_otp_user_id)
            target_email = user.email
            if user.profile.is_locked:
                return JsonResponse({'status': 'error', 'message': 'Account is locked'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=400)

    latest_otp = OTPVerification.objects.filter(
        email__iexact=target_email,
        purpose=purpose
    ).order_by('-created_at').first()

    if latest_otp:
        time_elapsed = now() - latest_otp.created_at
        if time_elapsed.total_seconds() < 30:
            remaining_cooldown = int(30 - time_elapsed.total_seconds())
            return JsonResponse({
                'status': 'error', 
                'message': f'Please wait {remaining_cooldown} seconds before requesting a new OTP.'
            }, status=400)

    OTPVerification.objects.filter(
        email__iexact=target_email,
        purpose=purpose,
        is_verified=False
    ).update(expires_at=now())

    otp_code = f"{secrets.randbelow(900000) + 100000:06d}"
    OTPVerification.objects.create(
        user=user,
        email=target_email,
        otp_hash=make_password(otp_code),
        purpose=purpose,
        expires_at=now() + timedelta(minutes=5)
    )

    # Write to debug log for local verification
    import os
    with open(os.path.join(settings.BASE_DIR, 'otp_debug.log'), 'a') as f:
        f.write(f"Resent OTP for {target_email}: {otp_code}\n")

    name = user.first_name if user else request.session.get('register_data', {}).get('fullname', 'User')
    subject = "CalmSphere - New Verification Code"
    message = f"Hello {name},\n\nYour new 6-digit verification code is: {otp_code}\nThis code is valid for 5 minutes.\n\nStay calm,\nCalmSphere Team"
    try:
        print(f"EMAIL DEBUG: Trying to resend email. Backend: {settings.EMAIL_BACKEND}, From: {settings.DEFAULT_FROM_EMAIL}, To: {target_email}")
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [target_email])
        print("EMAIL DEBUG: Resend email sent successfully.")
    except Exception as e:
        print("EMAIL ERROR:", e)
        return JsonResponse({
            'status': 'error',
            'message': 'Unable to send OTP email.'
            }, status=500)

    return JsonResponse({'status': 'success', 'message': 'OTP resent successfully.'})


def otp_success(request):
    next_url = request.session.pop('otp_success_next', 'mood')
    return render(request, 'otp_success.html', {'next_url': next_url})


import urllib.request
import urllib.error

@login_required
@csrf_exempt
def reading_progress(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            book_key = data.get("book_key")
            page = int(data.get("page", 0))
            sentence = int(data.get("sentence", 0))
            total_pages = int(data.get("total_pages", 1))
            
            percentage = (page / total_pages) * 100 if total_pages > 0 else 0.0
            if percentage > 100:
                percentage = 100.0
                
            progress, created = UserReadingProgress.objects.update_or_create(
                user=request.user,
                book_key=book_key,
                defaults={
                    'current_page': page,
                    'current_sentence': sentence,
                    'percentage_completed': percentage
                }
            )
            
            # Update reading streak if first activity today
            analytics, _ = ReadingAnalytics.objects.get_or_create(user=request.user)
            today = localdate()
            if analytics.last_reading_date != today:
                if analytics.last_reading_date == today - timedelta(days=1):
                    analytics.reading_streak += 1
                elif analytics.last_reading_date is None or (today - analytics.last_reading_date).days > 1:
                    analytics.reading_streak = 1
                analytics.last_reading_date = today
            
            # If bookmark page moved to the last page, check if we increment completed books
            if percentage >= 99.0 and not progress.percentage_completed >= 99.0:
                analytics.books_completed += 1
            
            # Simple pages completed calculation (optional increment)
            # We can count unique pages read, or just increment whenever a page is advanced
            if not created and progress.current_page < page:
                analytics.pages_completed += (page - progress.current_page)
            elif created:
                analytics.pages_completed += page
                
            analytics.save()
            return JsonResponse({"status": "success", "percentage": percentage})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@login_required
@csrf_exempt
def reading_track_time(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            track_type = data.get("type", "reading")
            seconds = int(data.get("seconds", 10))
            
            analytics, _ = ReadingAnalytics.objects.get_or_create(user=request.user)
            if track_type == "listening":
                analytics.total_listening_time += seconds
            else:
                analytics.total_reading_time += seconds
                
            # Update last active reading date and streak
            today = localdate()
            if analytics.last_reading_date != today:
                if analytics.last_reading_date == today - timedelta(days=1):
                    analytics.reading_streak += 1
                elif analytics.last_reading_date is None or (today - analytics.last_reading_date).days > 1:
                    analytics.reading_streak = 1
                analytics.last_reading_date = today
                
            analytics.save()
            return JsonResponse({
                "status": "success", 
                "reading_time": analytics.total_reading_time, 
                "listening_time": analytics.total_listening_time
            })
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@login_required
@csrf_exempt
def reading_ai(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
        action = data.get("action")
        text = data.get("text", "")
        question = data.get("question", "")
        book_title = data.get("book_title", "the book")
        
        api_key = request.headers.get("X-Gemini-Key") or request.session.get("gemini_key")
        
        # Simulated fallback if no API key is provided
        if not api_key:
            if action == "summarize":
                reply = f"Here is a summary of the current page of '{book_title}':\n\nThis section discusses how our mindset, habits, and environment shape our wellness journey. It emphasizes that real progress is not about massive sudden changes, but the steady application of small, daily modifications. Being aware of the present moment can significantly reduce anxiety and help you reclaim your focus."
            elif action == "explain":
                reply = f"Explanation for: \"{text}\"\n\nThis passage points out that we shouldn't let ourselves get overwhelmed by past regrets or future anxiety. The author suggests that focus and clarity reside strictly in the 'now', which is the only moment we truly have control over. By paying attention to small habits, we build a steady foundation for mental wellness."
            elif action == "key_points":
                reply = f"Key Points from this page of '{book_title}':\n\n1. **Mindset Matters**: Your perspective shapes your habits.\n2. **Small Shifts**: 1% daily improvement leads to exponential personal growth.\n3. **Present Awareness**: Peace is found when you quiet your thoughts and ground yourself in the now.\n4. **Quiet Progress**: Systems are more critical than goals alone."
            else: # chat
                reply = f"As your CalmSphere reading companion, I've analyzed your question about '{book_title}' ('{question}'). Reflecting on the context, this book guides you to build inner calm by breaking free from overthinking and practicing regular mindful awareness. Would you like me to summarize any specific page for you?"
            
            return JsonResponse({
                "status": "success", 
                "response": reply, 
                "simulated": True,
                "message": "Demo mode: Enter your Gemini API Key in AI Settings to enable real-time Gemini AI analysis!"
            })
        
        # Call Gemini REST API
        if action == "summarize":
            prompt = f"Provide a brief, clear, and calming summary of the following text from the book '{book_title}':\n\n{text}"
        elif action == "explain":
            prompt = f"Explain the following passage from the book '{book_title}' in simple, clear, and reassuring language suitable for a relaxation and wellness context:\n\n{text}"
        elif action == "key_points":
            prompt = f"Extract 3-4 key bullet points from the following text of the book '{book_title}':\n\n{text}"
        else: # chat
            prompt = f"The user is reading the book '{book_title}'. Based on the following page context:\n\"{text}\"\n\nAnswer the user's question in a calm, helpful, and professional tone:\n\"{question}\""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            gemini_text = res_data['candidates'][0]['content']['parts'][0]['text']
            
        return JsonResponse({"status": "success", "response": gemini_text, "simulated": False})
        
    except urllib.error.HTTPError as he:
        try:
            err_body = he.read().decode('utf-8')
            err_json = json.loads(err_body)
            err_msg = err_json.get("error", {}).get("message", str(he))
        except Exception:
            err_msg = str(he)
        return JsonResponse({"status": "error", "message": f"Gemini API Error: {err_msg}"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
