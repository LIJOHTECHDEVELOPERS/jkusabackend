# Admin Content Modules

This section covers content CRUD for admins and their public endpoints.

## Clubs
- Admin prefix: `/admin/clubs` | Public: `/clubs`
- Create: `POST /admin/clubs` (Form: name, description, logo)
- Read: `GET /admin/clubs` (paginated), `GET /admin/clubs/{id}`
- Update: `PUT /admin/clubs/{id}` (fields + logo upload/remove)
- Delete: `DELETE /admin/clubs/{id}`
- Public: `GET /clubs`, `GET /clubs/{id}`, `GET /clubs/slug/{slug}`

## Gallery
- Admin: `/admin/gallery` | Public: `/gallery`
- Create: `POST /admin/gallery` (Form: title, description?, category, year?, display_order?, image)
- Read: `GET /admin/gallery` (filters), `GET /admin/gallery/{id}`
- Update: `PUT /admin/gallery/{id}` (fields + image)
- Reorder: `PUT /admin/gallery/reorder` (body: `GalleryReorderRequest`)
- Delete: `DELETE /admin/gallery/{id}`
- Enums/Meta: `GET /admin/gallery/years/available`, `GET /admin/gallery/enums/categories`
- Public mirrors for list/detail, grouping by category, years and categories enums

## Activities
- Admin: `/admin/activities` | Public: `/activities`
- Create: `POST /admin/activities` (Form fields + optional image)
- List: `GET /admin/activities` (search, pagination)
- Detail: `GET /admin/activities/{id}`
- Update: `PUT /admin/activities/{id}` (fields + image handling)
- Delete: `DELETE /admin/activities/{id}`
- My activities: `GET /admin/activities/my/activities`
- Public mirrors for list/detail

## Events
- Admin: `/admin/events` | Public: `/events`
- Create: `POST /admin/events` (Form + image; slug auto)
- List: `GET /admin/events` (pagination)
- Detail: `GET /admin/events/{id}`
- Update: `PUT /admin/events/{id}` (fields + image, slug on title change)
- Delete: `DELETE /admin/events/{id}`
- Public: `GET /events`, `GET /events/{id}`, `GET /events/slug/{slug}`

## News
- Admin: `/admin/news` | Public: `/news`
- Create: `POST /admin/news` (Form + image; slug auto)
- List: `GET /admin/news` (pagination)
- Detail: `GET /admin/news/{id}`
- Update: `PUT /admin/news/{id}` (fields + image; slug on title change)
- Delete: `DELETE /admin/news/{id}`
- Public: `GET /news`, `GET /news/{id}`, `GET /news/slug/{slug}`

## Announcements
- Admin: `/admin/announcements` | Public: `/announcements`
- Create: `POST /admin/announcements` (Form + optional image) and sends emails to active students
- List: `GET /admin/announcements` (pagination)
- Detail: `GET /admin/announcements/{id}`
- Update: `PUT /admin/announcements/{id}` (fields + image; re-sends emails)
- Delete: `DELETE /admin/announcements/{id}`
- Public: `GET /announcements`, `GET /announcements/{id}`, `GET /announcements/latest/{count}`

## Resources
- Admin: `/admin/resources` | Public: `/resources`
- Create: `POST /admin/resources` (Form: title, description, pdf)
- List: `GET /admin/resources` (pagination)
- Detail: `GET /admin/resources/{id}`
- Update: `PUT /admin/resources/{id}` (fields + pdf replace/remove; slug updates on title)
- Delete: `DELETE /admin/resources/{id}`
- Public: `GET /resources`, `GET /resources/{id}`, `GET /resources/slug/{slug}`

## Leadership
- Admin: `/admin/leadership` | Public: `/leadership`
- Create: `POST /admin/leadership` (Form fields + optional profile_image)
- List: `GET /admin/leadership` (filters)
- Detail: `GET /admin/leadership/{id}`
- Update: `PUT /admin/leadership/{id}` (fields + image)
- Reorder: `PUT /admin/leadership/reorder`
- Delete: `DELETE /admin/leadership/{id}`
- Meta: `GET /admin/leadership/years/available`, `GET /admin/leadership/enums/campus-types`, `GET /admin/leadership/enums/leadership-categories`
- Public: list/detail plus `GET /leadership/organizational-structure`, meta endpoints
