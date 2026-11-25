.method public static c(Landroid/hardware/camera2/CaptureResult;)F
    .registers 5

    sget-object v0, LK5/K;->a:LK5/L;

    const v1, 0xbabe

    invoke-static {p0, v0, v1}, LK5/M;->h(Landroid/hardware/camera2/CaptureResult;LK5/L;I)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Ljava/lang/Float;

    if-eqz v0, :zeus_fallback

    invoke-virtual {v0}, Ljava/lang/Float;->floatValue()F

    move-result v0

    return v0

    # HAL has no focalLength35mm: zeus lens equivalent (mm) * zoom ratio
    :zeus_fallback
    const/high16 v0, 0x3f800000    # zoom = 1.0f

    sget-object v1, Landroid/hardware/camera2/CaptureResult;->CONTROL_ZOOM_RATIO:Landroid/hardware/camera2/CaptureResult$Key;

    invoke-virtual {p0, v1}, Landroid/hardware/camera2/CaptureResult;->get(Landroid/hardware/camera2/CaptureResult$Key;)Ljava/lang/Object;

    move-result-object v1

    check-cast v1, Ljava/lang/Float;

    if-eqz v1, :zoom_ok

    invoke-virtual {v1}, Ljava/lang/Float;->floatValue()F

    move-result v0

    :zoom_ok
    const/high16 v2, 0x41c00000    # 24.0f (main lens, logical cameras)

    sget-object v1, Landroid/hardware/camera2/CaptureResult;->LOGICAL_MULTI_CAMERA_ACTIVE_PHYSICAL_ID:Landroid/hardware/camera2/CaptureResult$Key;

    invoke-virtual {p0, v1}, Landroid/hardware/camera2/CaptureResult;->get(Landroid/hardware/camera2/CaptureResult$Key;)Ljava/lang/Object;

    move-result-object v1

    if-nez v1, :done

    sget-object v1, Landroid/hardware/camera2/CaptureResult;->LENS_FOCAL_LENGTH:Landroid/hardware/camera2/CaptureResult$Key;

    invoke-virtual {p0, v1}, Landroid/hardware/camera2/CaptureResult;->get(Landroid/hardware/camera2/CaptureResult$Key;)Ljava/lang/Object;

    move-result-object v1

    check-cast v1, Ljava/lang/Float;

    if-eqz v1, :done

    invoke-virtual {v1}, Ljava/lang/Float;->floatValue()F

    move-result p0

    const/high16 v1, 0x40400000    # 3.0f

    cmpg-float v1, p0, v1

    if-gez v1, :not_uw

    const/high16 v2, 0x41600000    # 14.0f (ultra-wide, 2.16 mm)

    goto :done

    :not_uw
    const/high16 v1, 0x40a00000    # 5.0f

    cmpg-float v1, p0, v1

    if-gez v1, :not_front

    const/high16 v2, 0x41c80000    # 25.0f (front, 3.26 mm)

    goto :done

    :not_front
    const/high16 v1, 0x40e00000    # 7.0f

    cmpl-float v1, p0, v1

    if-lez v1, :done

    const/high16 v2, 0x423c0000    # 47.0f (tele, 7.1 mm)

    :done
    mul-float/2addr v2, v0

    return v2
.end method
