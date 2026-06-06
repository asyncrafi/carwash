# User Profile Fixes

## Changes

### 1. `apps/accounts/serializers.py` — `UserSerializer`

- **Add `phone`** to `fields` list so it appears in `/api/auth/me/` response
- **Add `email`** to `read_only_fields` so users can't change their email via PATCH
- **Replace `avatar` field** with `SerializerMethodField` that returns absolute URL:

```python
class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'phone',
            'email', 'role', 'avatar',
            'is_verified', 'language', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'created_at']

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None
```

### 2. `apps/accounts/views.py` — Pass request context

Every place that instantiates `UserSerializer` needs `context={'request': request}`:

- **`RegisterView.post()`** (line ~80): `UserSerializer(user).data` → `UserSerializer(user, context={'request': request}).data`
- **`LoginView.post()`** (line ~106): `UserSerializer(user).data` → `UserSerializer(user, context={'request': request}).data`
- **`UserProfileView.get()`** (line ~213): `UserSerializer(request.user).data` → `UserSerializer(request.user, context={'request': request}).data`
- **`UserProfileView.patch()`** (line ~217-219): Already passes `data` and `partial`, just add `context={'request': request}`

### 3. `apps/accounts/views.py` — `AdminUserDetailView.patch()`

Line ~212 in `apps/admin_dashboard/views.py` also uses `UserSerializer(user, data=request.data, partial=True)` — needs `context={'request': request}` added too.

## Verification

After changes:
- `GET /api/auth/me/` returns: `{..., "phone": "+971501234567", "email": "john@...", "avatar": "http://localhost:8000/media/avatars/...", ...}`
- `PATCH /api/auth/me/` with `{"email": "new@..."}` ignores the email change (read-only)
- `PATCH /api/auth/me/` with `{"phone": "+33600000000"}` updates phone successfully
