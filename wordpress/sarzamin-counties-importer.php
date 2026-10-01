<?php
/**
 * Plugin Name: سرزمین آریان — ایمپورتر شهرستان‌ها
 * Description: درون‌ریزی مقاله‌های شهرستان‌ها از بستهٔ «ایمپورت» (data/counties.json + content/cities/*.html) به وردپرس؛ همراه با ثبت نوع محتوای «شهرستان» و تاکسونومی «استان».
 * Version: 1.0.0
 * Author: سرزمین آریان
 * Text Domain: sarzamin
 * Requires at least: 5.8
 * Requires PHP: 7.4
 * License: GPL-2.0-or-later
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

final class Sarzamin_Counties_Importer {

	const CPT      = 'city';
	const TAX      = 'province';
	const MENU     = 'sarzamin-counties-importer';
	const CAP      = 'manage_options';
	const NOTICE_K = 'sarzamin_import_notice_';

	public static function init() {
		add_action( 'init', array( __CLASS__, 'register_types' ) );
		add_action( 'admin_menu', array( __CLASS__, 'add_menu' ) );
		add_action( 'admin_post_sarzamin_import', array( __CLASS__, 'handle_import' ) );
	}

	/* --------------------------------------------------------------------- */
	/* نوع محتوا و تاکسونومی                                                  */
	/* --------------------------------------------------------------------- */

	public static function register_types() {
		register_post_type(
			self::CPT,
			array(
				'labels'       => array(
					'name'          => 'شهرستان‌ها',
					'singular_name' => 'شهرستان',
					'add_new_item'  => 'افزودن شهرستان',
					'edit_item'     => 'ویرایش شهرستان',
					'search_items'  => 'جست‌وجوی شهرستان',
				),
				'public'       => true,
				'has_archive'  => true,
				'menu_icon'    => 'dashicons-location-alt',
				'rewrite'      => array( 'slug' => 'city' ),
				'supports'     => array( 'title', 'editor', 'excerpt', 'thumbnail', 'revisions', 'custom-fields' ),
				'show_in_rest' => true,
			)
		);

		register_taxonomy(
			self::TAX,
			self::CPT,
			array(
				'labels'       => array(
					'name'          => 'استان‌ها',
					'singular_name' => 'استان',
				),
				'public'       => true,
				'hierarchical' => true,
				'rewrite'      => array( 'slug' => 'province' ),
				'show_in_rest' => true,
			)
		);
	}

	/* --------------------------------------------------------------------- */
	/* صفحهٔ مدیریت                                                          */
	/* --------------------------------------------------------------------- */

	public static function add_menu() {
		add_management_page(
			'ایمپورتر شهرستان‌ها',
			'ایمپورتر شهرستان‌ها',
			self::CAP,
			self::MENU,
			array( __CLASS__, 'render_page' )
		);
	}

	public static function render_page() {
		if ( ! current_user_can( self::CAP ) ) {
			wp_die( 'دسترسی مجاز نیست.' );
		}
		$default_path = WP_CONTENT_DIR . '/south-khorasan-counties';
		$notice       = get_transient( self::NOTICE_K . get_current_user_id() );
		if ( $notice ) {
			delete_transient( self::NOTICE_K . get_current_user_id() );
		}
		?>
		<div class="wrap" dir="rtl">
			<h1>ایمپورتر شهرستان‌ها — سرزمین آریان</h1>

			<?php if ( $notice ) : ?>
				<div class="notice notice-info"><pre style="white-space:pre-wrap;direction:rtl;"><?php echo esc_html( $notice ); ?></pre></div>
			<?php endif; ?>

			<p>
				این ابزار بستهٔ <code>data/counties.json</code> و متن‌های <code>content/cities/*.html</code> را می‌خواند و
				هر شهرستان را به‌صورت یک نوشتهٔ از نوع <strong>شهرستان</strong> (نشانی <code>/city/&lt;slug&gt;/</code>) با
				تاکنونومی <strong>استان</strong> (نشانی <code>/province/&lt;slug&gt;/</code>) درون‌ریزی می‌کند.
			</p>

			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
				<?php wp_nonce_field( 'sarzamin_import' ); ?>
				<input type="hidden" name="action" value="sarzamin_import" />

				<table class="form-table" role="presentation">
					<tr>
						<th scope="row"><label for="bundle_path">مسیر پوشهٔ بازشدهٔ بسته</label></th>
						<td>
							<input name="bundle_path" id="bundle_path" type="text" class="regular-text code"
								value="<?php echo esc_attr( get_option( 'sarzamin_bundle_path', $default_path ) ); ?>" dir="ltr" />
							<p class="description">پوشه‌ای که <code>data/counties.json</code> را در خود دارد.</p>
						</td>
					</tr>
					<tr>
						<th scope="row">وضعیت انتشار</th>
						<td>
							<label><input type="radio" name="post_status" value="draft" checked /> پیش‌نویس (پیشنهاد برای بازبینی)</label><br />
							<label><input type="radio" name="post_status" value="publish" /> انتشار مستقیم</label>
						</td>
					</tr>
					<tr>
						<th scope="row">تصویر شاخص</th>
						<td>
							<label><input type="checkbox" name="import_images" value="1" checked /> بارگذاری تصویر شاخص هر شهرستان از پوشهٔ <code>images/</code></label>
						</td>
					</tr>
					<tr>
						<th scope="row">آزمایش</th>
						<td>
							<label><input type="checkbox" name="dry_run" value="1" /> اجرای آزمایشی (بدون نوشتن در پایگاه‌داده)</label>
						</td>
					</tr>
				</table>

				<?php submit_button( 'اجرای ایمپورت' ); ?>
			</form>
		</div>
		<?php
	}

	/* --------------------------------------------------------------------- */
	/* ایمپورت                                                               */
	/* --------------------------------------------------------------------- */

	public static function handle_import() {
		if ( ! current_user_can( self::CAP ) ) {
			wp_die( 'دسترسی مجاز نیست.' );
		}
		check_admin_referer( 'sarzamin_import' );

		$bundle  = isset( $_POST['bundle_path'] ) ? sanitize_text_field( wp_unslash( $_POST['bundle_path'] ) ) : '';
		$status  = ( isset( $_POST['post_status'] ) && 'publish' === $_POST['post_status'] ) ? 'publish' : 'draft';
		$dry_run = ! empty( $_POST['dry_run'] );
		$images  = ! empty( $_POST['import_images'] );

		update_option( 'sarzamin_bundle_path', $bundle );

		$report = self::run( $bundle, $status, $dry_run, $images );

		set_transient( self::NOTICE_K . get_current_user_id(), $report, 5 * MINUTE_IN_SECONDS );
		wp_safe_redirect( admin_url( 'tools.php?page=' . self::MENU ) );
		exit;
	}

	private static function run( $bundle, $status, $dry_run, $images ) {
		$json_path = trailingslashit( $bundle ) . 'data/counties.json';
		if ( ! file_exists( $json_path ) ) {
			return "✗ فایل counties.json یافت نشد: {$json_path}";
		}
		$data = json_decode( file_get_contents( $json_path ), true );
		if ( ! is_array( $data ) || empty( $data['counties'] ) ) {
			return '✗ ساختار counties.json نامعتبر است.';
		}

		require_once ABSPATH . 'wp-admin/includes/file.php';
		require_once ABSPATH . 'wp-admin/includes/media.php';
		require_once ABSPATH . 'wp-admin/includes/image.php';

		$lines    = array();
		$lines[]  = sprintf(
			'استان: %s | تعداد: %d | وضعیت: %s | %s | تصاویر: %s',
			$data['province_name'],
			count( $data['counties'] ),
			$status,
			$dry_run ? 'اجرای آزمایشی' : 'اجرای واقعی',
			$images ? 'بله' : 'خیر'
		);
		$lines[] = '──────────────────────────────';

		// اطمینان از وجود ترم استان
		$province_slug = $data['province'];
		$province_name = $data['province_name'];
		$term          = term_exists( $province_slug, self::TAX );
		if ( ! $term && ! $dry_run ) {
			$term = wp_insert_term( $province_name, self::TAX, array( 'slug' => $province_slug ) );
		}

		foreach ( $data['counties'] as $c ) {
			$slug  = $c['slug'];
			$title = $c['title'];
			$html  = trailingslashit( $bundle ) . $c['html_file'];

			$existing = get_page_by_path( $slug, OBJECT, self::CPT );
			$action   = $existing ? 'به‌روزرسانی' : 'ایجاد';

			if ( ! file_exists( $html ) ) {
				$lines[] = "✗ {$slug}: فایل HTML یافت نشد ({$html})";
				continue;
			}
			$content = file_get_contents( $html );

			if ( $dry_run ) {
				$lines[] = "• [آزمایشی] {$action} — {$title} (/city/{$slug}/)";
				continue;
			}

			$postarr = array(
				'post_type'    => self::CPT,
				'post_status'  => $status,
				'post_title'   => $title,
				'post_name'    => $slug,
				'post_content' => $content,
				'post_excerpt' => isset( $c['excerpt'] ) ? $c['excerpt'] : '',
			);

			if ( $existing ) {
				$postarr['ID'] = $existing->ID;
				$post_id       = wp_update_post( $postarr, true );
			} else {
				$post_id = wp_insert_post( $postarr, true );
			}

			if ( is_wp_error( $post_id ) ) {
				$lines[] = "✗ {$slug}: " . $post_id->get_error_message();
				continue;
			}

			// تاکسونومی استان
			wp_set_object_terms( $post_id, $province_slug, self::TAX, false );

			// متادیتا
			update_post_meta( $post_id, '_sarzamin_province', $province_slug );
			update_post_meta( $post_id, '_sarzamin_province_name', $province_name );
			update_post_meta( $post_id, '_sarzamin_order', isset( $c['order'] ) ? (int) $c['order'] : 0 );
			update_post_meta( $post_id, '_sarzamin_image_alt', isset( $c['image_alt'] ) ? $c['image_alt'] : '' );
			update_post_meta( $post_id, '_sarzamin_image_path', isset( $c['image'] ) ? $c['image'] : '' );
			if ( ! empty( $c['focus_keywords'] ) ) {
				update_post_meta( $post_id, '_sarzamin_focus_keywords', implode( '، ', (array) $c['focus_keywords'] ) );
			}

			// تصویر شاخص
			if ( $images && ! has_post_thumbnail( $post_id ) && ! empty( $c['image_basename'] ) ) {
				$img = trailingslashit( $bundle ) . $c['image_basename'];
				if ( file_exists( $img ) ) {
					$tmp = wp_tempnam( basename( $img ) );
					copy( $img, $tmp );
					$file_array = array(
						'name'     => basename( $img ),
						'tmp_name' => $tmp,
					);
					$att_id = media_handle_sideload( $file_array, $post_id, isset( $c['image_alt'] ) ? $c['image_alt'] : '' );
					if ( ! is_wp_error( $att_id ) ) {
						set_post_thumbnail( $post_id, $att_id );
					} else {
						$lines[] = "  ⚠ تصویر {$slug}: " . $att_id->get_error_message();
					}
					if ( file_exists( $tmp ) ) {
						unlink( $tmp );
					}
				} else {
					$lines[] = "  ⚠ تصویر {$slug} یافت نشد ({$img})";
				}
			}

			$lines[] = "✓ {$action} — {$title} (#{$post_id} — /city/{$slug}/)";
		}

		$lines[] = '──────────────────────────────';
		$lines[] = 'پایان.';
		return implode( "\n", $lines );
	}
}

Sarzamin_Counties_Importer::init();

register_activation_hook(
	__FILE__,
	function () {
		Sarzamin_Counties_Importer::register_types();
		flush_rewrite_rules();
	}
);

register_deactivation_hook(
	__FILE__,
	function () {
		flush_rewrite_rules();
	}
);
