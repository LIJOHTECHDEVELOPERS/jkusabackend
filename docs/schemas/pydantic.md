# Schemas (Pydantic)

Key response/request models by module:

- `app/schemas/student.py`: `studentCreate`, `studentLogin`, `studentResponse`, `TokenData`, `PasswordResetRequest`, `PasswordResetConfirm`, `PasswordChange`, `CollegeResponse`, `SchoolResponse`
- `app/schemas/admin.py`: `AdminCreate`, `AdminUpdate`, `Admin`, `Token`, `TokenWithUser`, `AdminListResponse`
- `app/schemas/admin_role.py`: `AdminRoleCreate`, `AdminRoleUpdate`, `AdminRole`
- `app/schemas/announcement.py`: `AnnouncementCreate`, `Announcement`
- `app/schemas/event.py`: `EventCreate`, `Event`
- `app/schemas/gallery.py`: `GalleryCreate`, `GalleryUpdate`, `Gallery`, `GalleryReorderRequest`, `CategoryGalleryResponse`, `GallerySummary`
- `app/schemas/activity.py`: `ActivityCreate`, `ActivityUpdate`, `Activity`, `ActivityListResponse`
- `app/schemas/club.py`: `ClubCreate`, `Club`
- `app/schemas/news.py`: `NewsCreate`, `NewsUpdate`, `News`, `PublisherInfo`
- `app/schemas/resource.py`: `ResourceCreate`, `Resource`
- `app/schemas/lost_id.py`: `PostIDRequest`, `MarkCollectedRequest`, `LostIDResponse`, `LostIDListResponse`, `SystemInfoResponse`, `StationInfo`, `IDTypeInfo`, `SearchQuery`, `DeleteResponse`, `SuccessResponse`, `IDFilterParams`, `StationStatistics`, `DetailedStatisticsResponse`
- `app/schemas/subscriber.py`: `SubscriberCreate`, `SubscriberUpdate`, `Subscriber`, `SubscriberStats`, `SubscriberResponse`, `SubscriberListResponse`, `UnsubscribeRequest`, `BulkSubscriberCreate`, `BulkSubscriberResponse`, `SubscriberExport`
