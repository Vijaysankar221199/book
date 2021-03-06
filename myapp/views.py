from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render,get_object_or_404, redirect
from django import template
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login,logout
from datetime import datetime
from django.db import transaction
from myapp.forms import Authentic
from django.conf import settings
from django.contrib import messages
import os
from .forms import *
from .models import *
from django_otp.oath import totp
import time
import base64
from django.utils import timezone
from django.core.mail import EmailMessage
import smtplib

import os
import time
from twilio.rest import Client
from playsound import playsound
#account_sid = 'AC730d2142614ea4d8220278bb5bd247fd'
#auth_token = 'fdd8833312fe3d2ebc9eb7142c3cb771'
##################################################################
account_sid = 'ACdd9ee1f7f4f9c4254478af04c0e5f2e0'
auth_token = 'f591b18bfe88e2f89678fcf9699d7173'
client = Client(account_sid, auth_token)


def sms(msg, phn_number):
	message = client.messages \
	                .create(
	                     body=str(msg),
	                     from_='+12816128275',
	                     # from_='+15017122661',
	                     to='+91'+ str(phn_number)
	                 )

	print(message.sid)

# def call(phn):
# 	call = client.calls.create(
# 	                        twiml='<Response><Say>Alert!, You have a request</Say></Response>',
# 	                        to='+91'+str(phn),
# 	                        from_='+15093977702'
# 	                    )
#
# 	print(call.sid)


secret_key = b'12345678901234567890'


def mail (to_mail, visiname, slot_name):
	to_mail = to_mail
	visiname = visiname
	slot_name = slot_name
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login("authixx@gmail.com", "SHEERO12")
	message = visiname+  ", you Have Booked the slot " +slot_name+ ". Booking Confirmation is sent to mail and phone number "
	s.sendmail("authixx@gmail.com", to_mail, message)
	s.quit()


######################################################################
def index(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request,'security.html',)
            #return HttpResponseRedirect('/admin/')
        else:
            user = request.user.username
            check = Profile.objects.filter(user=user)
            if check:
            	return render(request,'inmates.html',)
            else:
                return render(request,'inmates - noprof.html',)
			#rreturn HttpResponseRedirect('index')
    else:
        return render(request,'index.html',)

@login_required
def dashboard(request):
    if request.user.is_superuser:
        return render(request,'security.html',)
    else:
        return render(request,'inmates.html',)


@login_required
@transaction.atomic
def myupdate(request):
    if request.method == 'POST':

        profile_form = ProfileForm(request.POST, request.FILES)
        if  profile_form.is_valid():
            comment = profile_form.save(commit=False)
            comment.user = request.user.username
            comment.save()
            #profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return HttpResponseRedirect(reverse('index',))
        else:
            messages.error(request, 'Please correct the error below.')
    else:

        profile_form = ProfileForm()
    return render(request, 'profile.html', {

        'profile_form': profile_form
    })


@login_required
def verify_otp(request):
    if request.user.is_superuser:
        if request.method =='POST':
            username=request.POST.get("username")
            print (username)
            password=request.POST.get("password")
            try:
                originaluser = otp.objects.filter(name=username)
                length = len(originaluser)
                print(length)
                originaluser= originaluser[length-1]
                if originaluser:
                    if originaluser.otp == password:
                        return HttpResponse("verified and allow")
                    else:
                        return HttpResponse("invalid OTP")
            except:
                return HttpResponse("invalid name")


        return render(request,'verify_OTP.html',)
    else:
        return HttpResponse("OTP Verify", content_type='text/plain')



@login_required
def myexpected(request):
    if request.user.is_superuser:
        return HttpResponse("NOT VALID", content_type='text/plain')
    else:
        if request.method == 'GET':
            username = request.user.username
            Image2 = scanupload.objects.filter(status= 'allow')
            stu = {"details": Image2 }
            return render(request,'Request_handling.html',stu)
        elif request.method == 'POST':
            if 'Book' in request.POST :
                visiname = request.user.username
                slot  = scanupload.objects.get(slot_name=request.POST.get("student_id"))
                slot_name = slot.slot_name
                slot.status = 'occupied'
                slot.visiname = visiname
                #slot.save()
                print(slot.status)
                now = timezone.now()
                #visiname = request.user.username
                profile =  Profile.objects.filter(user = visiname).first()
                car_number = profile.car_number
                phone = profile.Phonenumber
                slot.car_number = car_number
                slot.Phonenumber = phone

                store_all = allbookings.objects.create(slot_name= slot_name,visiname=visiname,
status='occupied',car_number=car_number,Phonenumber = phone)


                # for delta in range(10,110,20):
                #     otplist.append(totp(key=secret_key, step=10, digits=6, t0=(now-delta)))
                otpnumber= visiname + ", you Have Booked " + slot_name
                number = '8072366581'
                print(number)
                email_id =  request.user.email
                print(email_id)
                mail(email_id, visiname, slot_name)
                #email = EmailMessage('Subject', 'Body','authixx@gmail.com', to=['vvs221199@email.com'])
                #email.send()
                #sms (str(otpnumber),number)
                slot.save()
                message = f" {visiname}  you Have Booked  {slot_name}. Booking Confirmation is sent to mail and phone number "
                return HttpResponse(message, content_type='text/plain')
            elif 'No' in request.POST :
                team = expectedvisitor.objects.get(id=request.POST.get("student_id"))
                number = team.phone
                message = f"Acknowledgment is resent to {number}"
                return HttpResponse(message, content_type='text/plain')

        #return HttpResponse("OTP sent to ", content_type='text/plain')


@login_required
def addslot(request):
    listdetails =[]
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            return redirect('index')
    else:
        form = UploadForm()


    return render(request,'awards.html',{'form' : form})

@login_required
def request_status(request):
    if request.user.is_superuser:
        if request.method == 'GET':
            Image = allbookings.objects.all()
            #Image = Image.order_by('-id')
            #print (Image)
            #print(type(Image))

            stu = {"details": Image }
            return render(request,'request_status.html',stu)


    else:
        if request.method == 'POST':
            if 'Cancel' in request.POST :
                team = scanupload.objects.get(slot_name=request.POST.get("student_id"))
                if team.status == 'occupied':
                    team.status = 'allow'
                    team.save(update_fields=['status'])
                    team.save()


        else:
            username = request.user.username
            Image1 = scanupload.objects.filter(visiname = username , status='occupied')
            print(Image1)
            Image1 = Image1.order_by('-id')
            profile = Profile.objects.filter(user = username).first()
            #combined_query = profile.union(Image1)
            print(profile.car_number)
            stu1 = {"details": Image1}
            print (stu1)
            return render(request,'mybook.html',stu1)


        #return render(request,'Request_handling.html',stu1)
        return HttpResponse("okay", content_type='text/plain')

@login_required
def allbook(request):
    if request.user.is_superuser:
        if request.method == 'GET':
            Image1 = scanupload.objects.all()
	#Image1 = Image1.order_by('-id')
            stu1 = {"details": Image1}
            print (stu1)
            return render(request,'Request.html',stu1)
        elif request.method == 'POST':
            if 'Remove' in request.POST :
                team = scanupload.objects.get(slot_name=request.POST.get("student_id"))
			#profile = Profile.objects.filter(user = team.username)
                if team.status == 'occupied' or team.status!='NONE':
                    team.status = 'allow'
                    team.visiname = 'NONE'
                    team.car_number = 'NONE'
                    team.Phonenumber = "NONE"
                    team.save()
                return HttpResponse("Removed", content_type='text/plain')


@login_required
def user_logout(request):
    #instance = allbookings.objects.all()
    #instance.delete()
    logout(request)
    return HttpResponseRedirect(reverse('index'))


@login_required
def passvalidate(request):
        if request.method=="POST":
            username=request.POST.get("username")
            password=request.POST.get("password")

            user=authenticate(username=username,password=password)

            if user:
                print ("password validation is succesful")
                return HttpResponse("password validation is succesful", content_type='text/plain')

            else:
                print("invalid username and password")
                return HttpResponse("wrong credantials", content_type='text/plain')

        else :
            return render(request,'passvalidate.html',)


# Create your views here.
def user_login(request):
    if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('index'))
    else:
        if request.method=="POST":
            username=request.POST.get("username")
            password=request.POST.get("password")

            user=authenticate(username=username,password=password)

            if user:
                login(request,user)
                return HttpResponseRedirect(reverse('index',))
            else:
                return HttpResponse("invalid username and password")
        else :
            return render(request,'login.html',)


def authentication_view(request):
    registered = False

    if request.method=="POST":
        #print(request.POST)
        auth=Authentic(request.POST )

        if auth.is_valid():
            auth=auth.save(commit=False)
            auth.set_password(auth.password)
            #hashing the password
            auth.save()
            registered=True
        else :
            print("error")
    else:
        auth=Authentic()
    return render(request,'login.html',)
