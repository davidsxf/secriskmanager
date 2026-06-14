from django import forms

from .models import MaliciousIP, SourcePreset, Tag

TAILWIND_INPUT = (
    "block w-full rounded-md border-gray-300 shadow-sm "
    "focus:border-blue-500 focus:ring-blue-500 "
    "text-base py-3 px-4"
)
TAILWIND_SELECT = TAILWIND_INPUT
TAILWIND_TEXTAREA = TAILWIND_INPUT + " resize-vertical"


class MaliciousIPForm(forms.ModelForm):
    source = forms.ChoiceField(
        label="来源",
        choices=[],  # 在 __init__ 中填充
        widget=forms.Select(attrs={"class": TAILWIND_SELECT}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sources = SourcePreset.objects.all()
        self.fields["source"].choices = [
            (s.slug, f"{'🔄 ' if not s.is_manual else '✏️ '}{s.name}")
            for s in sources
        ]

    class Meta:
        model = MaliciousIP
        fields = [
            "ip_address",
            "cidr",
            "range_start",
            "range_end",
            "source",
            "category",
            "confidence",
            "is_active",
            "tags",
            "remark",
        ]
        widgets = {
            "ip_address": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "例如 192.168.1.1",
                }
            ),
            "cidr": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "例如 10.0.0.0/8",
                }
            ),
            "range_start": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "范围起始 IP",
                }
            ),
            "range_end": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "范围结束 IP",
                }
            ),
            "category": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "例如 malware / phishing / botnet",
                }
            ),
            "confidence": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "min": 0, "max": 100}
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}
            ),
            "tags": forms.SelectMultiple(
                attrs={"class": TAILWIND_SELECT}
            ),
            "remark": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA,
                    "rows": 3,
                    "placeholder": "备注信息",
                }
            ),
        }


class MaliciousIPImportForm(forms.Form):
    ip_file = forms.FileField(
        label="选择 IP 文件",
        help_text="支持 .conf 或 .txt 格式（每行一个 IP/CIDR/范围）",
        widget=forms.FileInput(
            attrs={
                "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 "
                "file:rounded-md file:border-0 file:text-sm file:font-medium "
                "file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100",
            }
        ),
    )
    source = forms.ChoiceField(
        label="来源",
        choices=[],
        widget=forms.Select(attrs={"class": TAILWIND_SELECT}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sources = SourcePreset.objects.all()
        self.fields["source"].choices = [
            (s.slug, f"{'🔄 ' if not s.is_manual else '✏️ '}{s.name}")
            for s in sources
        ]


class MaliciousIPDiffForm(forms.Form):
    conf_file = forms.FileField(
        label="选择设备导出的 .conf 文件",
        help_text="上传安全设备现有的 IP 组文件进行比对",
        widget=forms.FileInput(
            attrs={
                "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 "
                "file:rounded-md file:border-0 file:text-sm file:font-medium "
                "file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100",
            }
        ),
    )


class MaliciousIPLookupForm(forms.Form):
    query = forms.CharField(
        label="IP 地址 / CIDR / 范围",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": TAILWIND_INPUT,
                "placeholder": "例如 192.168.1.1 或 10.0.0.0/8",
            }
        ),
    )
