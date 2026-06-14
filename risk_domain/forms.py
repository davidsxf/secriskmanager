from django import forms

from .models import MaliciousDomain

TAILWIND_INPUT = (
    "block w-full rounded-md border-gray-300 shadow-sm "
    "focus:border-blue-500 focus:ring-blue-500 "
    "text-base py-3 px-4"
)
TAILWIND_TEXTAREA = TAILWIND_INPUT + " resize-vertical"


class MaliciousDomainForm(forms.ModelForm):
    class Meta:
        model = MaliciousDomain
        fields = ["domain", "prefix_at", "source", "category", "is_active", "remark"]
        widgets = {
            "domain": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "例如 example.com",
                }
            ),
            "prefix_at": forms.CheckboxInput(
                attrs={
                    "class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                }
            ),
            "source": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "category": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "例如 phishing / malware",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                }
            ),
            "remark": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA,
                    "rows": 3,
                    "placeholder": "备注信息",
                }
            ),
        }


class MaliciousDomainImportForm(forms.Form):
    txt_file = forms.FileField(
        label="选择 .txt 文件",
        help_text="上传安全设备导出的域名组文件（每行一个域名）",
        widget=forms.FileInput(
            attrs={
                "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 "
                "file:rounded-md file:border-0 file:text-sm file:font-medium "
                "file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100",
            }
        ),
    )


class MaliciousDomainDiffForm(forms.Form):
    txt_file = forms.FileField(
        label="选择设备导出的 .txt 文件",
        help_text="上传安全设备现有的域名组文件进行比对",
        widget=forms.FileInput(
            attrs={
                "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 "
                "file:rounded-md file:border-0 file:text-sm file:font-medium "
                "file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100",
            }
        ),
    )
