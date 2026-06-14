from django import forms

from .models import LocalAsset

TAILWIND_INPUT = "block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-base py-3 px-4"
TAILWIND_TEXTAREA = TAILWIND_INPUT + " resize-vertical"


class LocalAssetForm(forms.ModelForm):
    class Meta:
        model = LocalAsset
        fields = ["ip_address", "mac_address", "hostname", "person_name", "department", "device_type", "remark"]
        widgets = {
            "ip_address": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "例如 192.168.1.1"}),
            "mac_address": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "xx:xx:xx:xx:xx:xx"}),
            "hostname": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "主机名"}),
            "person_name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "姓名"}),
            "department": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "部门"}),
            "device_type": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "remark": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class LocalAssetImportForm(forms.Form):
    conf_file = forms.FileField(
        label="选择 ipmacdesc.conf 文件",
        widget=forms.FileInput(attrs={
            "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100",
        }),
    )


class LocalAssetBindCommandForm(forms.Form):
    selected_ids = forms.CharField(widget=forms.HiddenInput(), required=False)
    vlan = forms.IntegerField(
        label="VLAN ID",
        min_value=1, max_value=4094,
        initial=1,
        widget=forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
    )
