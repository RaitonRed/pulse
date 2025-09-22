from django.db import models

# Left Nav Tweet form processing
def left_nav_tweet_form_processing(request, Tweet, current_basic_user_profile):
    if request.POST.get("hidden_panel_tweet_submit_btn"):
        tweet_content = request.POST.get("tweet_content")
        tweet_image = request.FILES.get("tweet_image")

        new_tweet = Tweet(
            user=current_basic_user_profile, content=tweet_content,
            image=tweet_image
        )
        new_tweet.save()


# Mobile tweet form processing
def mobile_tweet_form_processing(request, Tweet, current_basic_user_profile):
    if request.POST.get("mobile_hidden_tweet_submit_btn"):
        tweet_content = request.POST.get("tweet_content")
        tweet_image = request.FILES.get("tweet_image")

        new_tweet = Tweet(
            user=current_basic_user_profile, content=tweet_content,
            image=tweet_image
        )
        new_tweet.save()


# Who to follow box cells
def get_who_to_follow(BasicUserProfile, ObjectDoesNotExist, random):
    try:
        # دریافت تمامی کاربران
        all_users = list(BasicUserProfile.objects.all())
        
        # اگر کاربری وجود ندارد، لیست خالی بازگردانده شود
        if not all_users:
            return []
            
        # اگر تعداد کاربران کمتر یا مساوی ۳ باشد، همه را بازگردان
        if len(all_users) <= 3:
            return all_users
            
        # انتخاب تصادفی ۳ کاربر منحصر به فرد
        who_to_follow = random.sample(all_users, 3)
        return who_to_follow
        
    except ObjectDoesNotExist:
        return []


# Topics to follow
def get_topics_to_follow(Topic, ObjectDoesNotExist, random):
    try:
        popular_topic = Topic.objects.annotate(
            tweet_count=models.Count('tweet')
        ).order_by('-tweet_count')[:5]
        return list(popular_topic)
    except ObjectDoesNotExist:
        return []