from django.shortcuts import render

def is_ajax(request):
    """
    Check if the request is an AJAX request.
    """
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def render_template(request, template_name, context=None):
    """
    Render the appropriate template based on whether the request is AJAX or not.
    
    If it's an AJAX request, render only the content block.
    Otherwise, render the full template.
    """
    if context is None:
        context = {}
        
    # If it's an AJAX request, we only need to return the content
    if is_ajax(request):
        # Append _content to the template name for AJAX requests
        # This allows us to create special templates for AJAX responses if needed
        content_template = template_name
        return render(request, content_template, context)
    else:
        # Regular request, render the full template
        return render(request, template_name, context)
