from django.shortcuts import render

def time_in(request):
    """Time In page for face recognition attendance"""
    return render(request, 'face_recognition/time_in.html')

def time_out(request):
    """Time Out page for face recognition attendance"""
    return render(request, 'face_recognition/time_out.html')
