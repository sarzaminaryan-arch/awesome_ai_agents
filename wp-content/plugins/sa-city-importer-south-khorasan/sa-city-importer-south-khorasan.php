<?php
/**
 * Plugin Name: سرزمین آریان — درون‌ریز شهرستان‌های استان خراسان جنوبی
 * Plugin URI:  https://github.com/sarzaminaryan-arch/awesome_ai_agents
 * Description: درون‌ریز کامل ۱۲ شهرستان آمادهٔ استان خراسان جنوبی (بیرجند، بشرویه، خوسف، درمیان، زیرکوه، سرایان، سربیشه، طبس، فردوس، قائنات، نهبندان، عشق‌آباد) — متن کامل مقاله (بلوک‌های گوتنبرگ)، جدول‌ها، پرسش‌های متداول (FAQ)، فهرست منابع، فیلدهای مدل داده (sa_city_*، sa_access_*، sa_google_map_url)، اسکیمای City+TouristDestination، سئو رنک‌مث، ارتباط با برگهٔ مادر استان و آپلود تصویر شاخص وب‌پی همراه هر صفحه؛ با قابلیت درون‌ریزی به‌صورت پیش‌نویس یا انتشار مستقیم.
 * Version:     1.0.0
 * Requires at least: 6.0
 * Requires PHP: 7.4
 * Author:      سرزمین آریان
 * Author URI:  https://sarzaminaryan.ir
 * License:     GPLv2 or later
 * License URI: http://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: sa-province-importer
 *
 * @package Sarzaminaryan_City_Importer
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'SA_CI_SOUTH_KHORASAN_VERSION', '1.0.0' );
define( 'SA_CI_SOUTH_KHORASAN_FILE', __FILE__ );

require_once __DIR__ . '/includes/class-sa-city-importer.php';

/**
 * Register this plugin's data batch with the city importer core.
 */
function sa_ci_south_khorasan_register() {
	SA_City_Province_Importer::instance()->register_batch(
		array(
			'id'          => 'south-khorasan',
			'dir'         => __DIR__ . '/data',
			'plugin_file' => __FILE__,
			'version'     => SA_CI_SOUTH_KHORASAN_VERSION,
		)
	);
}
add_action( 'plugins_loaded', 'sa_ci_south_khorasan_register', 20 );

/**
 * افزودن لینک مستقیم «درون‌ریزی و انتشار» در صفحهٔ افزونه‌ها و زیرمنوی «شهرها»
 */
function sa_ci_south_khorasan_action_links( $links ) {
	$url = admin_url( 'admin.php?page=sa-city-importer-south-khorasan' );
	array_unshift( $links, '<a href="' . esc_url( $url ) . '" style="font-weight:700;color:#0a7d33;">درون‌ریزی و انتشار شهرستان‌ها</a>' );
	return $links;
}
add_filter( 'plugin_action_links_' . plugin_basename( __FILE__ ), 'sa_ci_south_khorasan_action_links' );

function sa_ci_south_khorasan_submenu() {
	add_submenu_page(
		'edit.php?post_type=city',
		'درون‌ریز خراسان جنوبی',
		'درون‌ریز خراسان جنوبی',
		'manage_options',
		'sa-city-importer-south-khorasan',
		array( SA_City_Province_Importer::instance(), 'render_page' )
	);
}
add_action( 'admin_menu', 'sa_ci_south_khorasan_submenu', 45 );

/**
 * یکسان‌سازی نامک‌های قدیمی (در صورت وجود پیش‌نویس‌های خام قبلی) و پشتیبانی از انتشار مستقیم
 */
function sa_ci_south_khorasan_pre_import() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	$batch_id = isset( $_POST['batch'] ) ? sanitize_key( wp_unslash( $_POST['batch'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Missing
	if ( 'south-khorasan' !== $batch_id ) {
		return;
	}
	$legacy_map = array(
		'beshrooyeh' => 'boshruyeh',
		'khosf' => 'khusf',
		'asadieh' => 'darmiyan',
		'hajjiabad' => 'zirkuh',
		'ghaen' => 'qayenat',
		'torbat-jam' => 'torbatjam',
	);
	foreach ( $legacy_map as $old_slug => $new_slug ) {
		$old_posts = get_posts(
			array(
				'post_type'      => 'city',
				'post_status'    => array( 'publish', 'draft', 'pending', 'private', 'future' ),
				'name'           => $old_slug,
				'posts_per_page' => 1,
				'fields'         => 'objects',
				'no_found_rows'  => true,
			)
		);
		$new_posts = get_posts(
			array(
				'post_type'      => 'city',
				'post_status'    => array( 'publish', 'draft', 'pending', 'private', 'future' ),
				'name'           => $new_slug,
				'posts_per_page' => 1,
				'fields'         => 'ids',
				'no_found_rows'  => true,
			)
		);
		if ( $old_posts && ! $new_posts ) {
			wp_update_post(
				array(
					'ID'        => $old_posts[0]->ID,
					'post_name' => $new_slug,
				)
			);
			add_post_meta( $old_posts[0]->ID, '_wp_old_slug', $old_slug );
		}
	}
}
add_action( 'admin_post_sa_city_import', 'sa_ci_south_khorasan_pre_import', 5 );

/**
 * ثبت ریدایرکت نامک‌های قدیمی (_wp_old_slug) و اعمال انتشار مستقیم در صورت انتخاب کاربر
 */
function sa_ci_south_khorasan_post_meta_hook( $meta_id, $post_id, $meta_key, $meta_value ) {
	if ( '_sa_import_time' !== $meta_key ) {
		return;
	}
	if ( 'south-khorasan' !== get_post_meta( $post_id, '_sa_import_batch', true ) ) {
		return;
	}
	if ( ! get_post_meta( $post_id, 'sa_province_id', true ) && post_type_exists( 'province' ) ) {
		$hub = get_posts(
			array(
				'post_type'      => 'province',
				'post_status'    => array( 'publish', 'draft', 'pending', 'private', 'future' ),
				'name'           => 'south-khorasan',
				'posts_per_page' => 1,
				'fields'         => 'ids',
				'no_found_rows'  => true,
			)
		);
		if ( $hub ) {
			update_post_meta( $post_id, 'sa_province_id', (int) $hub[0] );
		}
	}
	$slug = get_post_meta( $post_id, 'sa_city_slug', true );
	$aliases = array(
		'boshruyeh' => 'beshrooyeh',
		'khusf'     => 'khosf',
		'darmiyan'  => 'asadieh',
		'zirkuh'    => 'hajjiabad',
		'qayenat'   => 'ghaen',
		'torbatjam' => 'torbat-jam',
	);
	if ( isset( $aliases[ $slug ] ) ) {
		$old = $aliases[ $slug ];
		$existing_olds = get_post_meta( $post_id, '_wp_old_slug', false );
		if ( ! in_array( $old, (array) $existing_olds, true ) ) {
			add_post_meta( $post_id, '_wp_old_slug', $old );
		}
	}
	if ( ! empty( $_POST['opt_publish_now'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Missing
		wp_update_post(
			array(
				'ID'          => $post_id,
				'post_status' => 'publish',
			)
		);
	}
}
add_action( 'added_post_meta', 'sa_ci_south_khorasan_post_meta_hook', 10, 4 );
add_action( 'updated_post_meta', 'sa_ci_south_khorasan_post_meta_hook', 10, 4 );

/**
 * افزودن گزینهٔ «انتشار مستقیم پس از درون‌ریزی» به فرم درون‌ریز (حتی اگر هستهٔ قدیمی‌تر فعال باشد)
 */
function sa_ci_south_khorasan_inject_publish_option() {
	$page = isset( $_GET['page'] ) ? sanitize_key( wp_unslash( $_GET['page'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
	if ( 'sa-city-importer-south-khorasan' !== $page ) {
		return;
	}
	?>
	<script>
	jQuery(function($){
		var $form = $('form input[name="batch"][value="south-khorasan"]').closest('form');
		if ($form.length && !$form.find('input[name="opt_publish_now"]').length) {
			var $lastCheck = $form.find('input[name="opt_overwrite_featured"]').closest('p');
			if ($lastCheck.length) {
				$lastCheck.append('<br /><label style="font-weight:700;color:#0a7d33;"><input type="checkbox" name="opt_publish_now" value="1" checked="checked" /> انتشار مستقیم نوشته‌ها پس از درون‌ریزی (Publish — آماده‌ی نمایش در سایت)</label>');
			}
		}
	});
	</script>
	<?php
}
add_action( 'admin_footer', 'sa_ci_south_khorasan_inject_publish_option' );
